import uuid
from collections.abc import Sequence, Iterable

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.order_item import OrderItem

from decimal import Decimal

class OrderRepository:
    """Доступ к данным заказов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Возвращает заказ вместе с позициями.

        Args:
            order_id: Идентификатор заказа.

        Returns:
            Заказ с загруженными позициями или `None`, если не найден.
        """
        stmt = (
            select(Order)
            .where(Order.order_id == order_id)
            .options(selectinload(Order.items))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        """Возвращает заказ по ключу идемпотентности.

        Args:
            idempotency_key: Ключ идемпотентности заказа.

        Returns:
            Заказ с загруженными позициями или `None`, если не найден.
        """
        stmt = (
            select(Order)
            .where(Order.idempotency_key == idempotency_key)
            .options(selectinload(Order.items))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _list_conditions(
        self,
        *,
        status: OrderStatus | None,
        email: str | None,
    ) -> list[ColumnElement[bool]]:
        """Собирает условия WHERE для списка заказов.

          Args:
            status: Фильтр по статусу заказа.
            email: Фильтр по email покупателя. Ожидается уже
                нормализованным (нижний регистр) — репозиторий сам
                регистр не приводит, это забота сервисного/API-слоя.

        Returns:
            Список условий для передачи в `.where(*conditions)`.
        """
        conditions: list[ColumnElement[bool]] = []
        if status is not None:
            conditions.append(Order.status == status.value)
        if email is not None:
            conditions.append(Order.email == email)
        return conditions

    async def list_orders(
        self,
        *,
        status: OrderStatus | None = None,
        email: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Order], int]:
        """Возвращает страницу заказов и общее их количество.

        Args:
            status: Фильтр по статусу заказа.
            email: Фильтр по email покупателя (уже нормализованный).
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка заказов (с загруженными позициями) и
            общего количества подходящих записей.
        """
        conditions = self._list_conditions(status=status, email=email)

        items_stmt = (
            select(Order)
            .where(*conditions)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc(), Order.order_id)
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(Order).where(*conditions)

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def update_status(self, order: Order, new_status: OrderStatus) -> Order:
        """Меняет статус заказа.

        Args:
            order: Существующий ORM-объект заказа (обычно результат
                `get_by_id`, то есть уже с загруженными позициями).
            new_status: Новый статус заказа.

        Returns:
            Обновлённый ORM-объект заказа с сохранённой связью `items`.
        """
        order.status = new_status.value
        await self._session.flush()
        await self._session.refresh(order, attribute_names=["status", "updated_at"])
        return order

class OrderRepositorySagaMethods:
    """Методы, которые нужно добавить в `OrderRepository`."""
 
    _session: object  # в реальном классе — AsyncSession из __init__
 
    async def create_pending(
        self,
        *,
        idempotency_key: str,
        user_name: str,
        phone: str,
        email: str,
        delivery_address: str,
    ) -> Order:
        """Создаёт заказ в статусе `pending` с нулевой суммой.
 
        `order_id` генерируется в Python до любых сетевых вызовов и служит
        ключом идемпотентности операций резервирования в products_service.
 
        Args:
            idempotency_key: Ключ идемпотентности из запроса.
            user_name: Имя покупателя.
            phone: Телефон покупателя.
            email: Email покупателя в нижнем регистре.
            delivery_address: Адрес доставки.
 
        Returns:
            Ещё не закоммиченный объект заказа с заполненным `order_id`.
        """
        order = Order(
            order_id=uuid.uuid4(),
            idempotency_key=idempotency_key,
            user_name=user_name,
            phone=phone,
            email=email,
            delivery_address=delivery_address,
            total_price=Decimal("0.00"),
            status=OrderStatus.PENDING.value,
        )
        self._session.add(order)
        await self._session.flush()
        return order
 
    def add_items(self, items: Iterable[OrderItem]) -> None:
        """Добавляет позиции заказа в сессию.
 
        Метод синхронный: `add_all` не ходит в БД, запись произойдёт при
        ближайшем flush или commit.
 
        Args:
            items: Готовые объекты позиций заказа.
        """
        self._session.add_all(list(items))
 
    async def mark_new(self, order_id: uuid.UUID, total_price: Decimal) -> int:
        """Переводит заказ из `pending` в `new` и проставляет сумму.
 
        Условие `status = 'pending'` в WHERE — защита от параллельного
        изменения строки: если статус уже сменили, обновление просто
        не найдёт запись и вернёт 0.
 
        Args:
            order_id: Идентификатор заказа.
            total_price: Итоговая сумма заказа.
 
        Returns:
            Количество обновлённых строк: 1 при успехе, 0 если заказ уже
            не в статусе `pending`.
        """
        stmt = (
            update(Order)
            .where(
                Order.order_id == order_id,
                Order.status == OrderStatus.PENDING.value,
            )
            .values(status=OrderStatus.NEW.value, total_price=total_price)
        )
        result = await self._session.execute(stmt)
        return result.rowcount or 0
 
    async def set_status_by_id(self, order_id: uuid.UUID, new_status: OrderStatus) -> int:
        """Безусловно проставляет статус заказа по идентификатору.
 
        Отличается от существующего `update_status` тем, что не требует
        загруженного ORM-объекта: в саге заказ переводится в `failed`
        уже после отката сессии, когда объект может быть невалиден.
 
        Args:
            order_id: Идентификатор заказа.
            new_status: Новый статус.
 
        Returns:
            Количество обновлённых строк.
        """
        stmt = (
            update(Order)
            .where(Order.order_id == order_id)
            .values(status=new_status.value)
        )
        result = await self._session.execute(stmt)
        return result.rowcount or 0