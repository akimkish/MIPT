"""Репозиторий доступа к таблице заказов."""

import uuid
from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus
from app.models.order import Order


class OrderRepository:
    """Доступ к данным заказов.

    На этом этапе — только чтение и смена статуса: создание заказа
    требует вызовов products_service и появится на Этапе 7. Позиции
    заказа (`OrderItem`) отдельного репозитория не имеют — они всегда
    читаются вместе с заказом через `selectinload` и не изменяются
    сами по себе (неизменяемый снимок).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Возвращает заказ вместе с позициями.

        Позиции грузятся всегда, а не по требованию: `OrderRead`
        отдаёт их в каждом ответе (см. схему), а в async-режиме
        отложенная подгрузка `order.items` при сериализации привела бы
        к ошибке доступа к неинициализированному атрибуту.

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

        Метод не используется до Этапа 7 (оформление заказа сверяет по
        нему повторную отправку формы), но заведён уже сейчас: поле
        `idempotency_key` уникально на уровне БД, и находить заказ по
        нему — обычная операция чтения, не завязанная на логику
        создания.

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

        Вынесено отдельно, чтобы запрос страницы и запрос `COUNT(*)`
        использовали одинаковый набор фильтров — тот же приём, что и в
        `ProductRepository._catalog_conditions`.

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

        `refresh` ограничен именно изменёнными колонками
        (`attribute_names=["status", "updated_at"]`), а не вызывается без
        аргументов: полный refresh экспирует ВСЕ атрибуты объекта, включая
        уже загруженную через selectinload связь `items` — и следующее
        обращение к `order.items` (например, при сериализации в OrderRead)
        попыталось бы лениво подгрузить её вне await-контекста, что в
        AsyncSession технически невозможно (нет greenlet для I/O) и
        выглядит как ошибка валидации Pydantic на поле items.

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
