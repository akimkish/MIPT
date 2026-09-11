import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.order_status import is_transition_allowed
from app.models.enums import OrderStatus
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.services.exceptions import ConflictError, NotFoundError


class OrderService:
    """Сценарии чтения заказов и смены их статуса."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session
        self._repository = OrderRepository(session)

    async def get(self, order_id: uuid.UUID) -> Order:
        """Возвращает заказ с позициями по идентификатору.

        Args:
            order_id: Идентификатор заказа.

        Returns:
            Найденный заказ.

        Raises:
            NotFoundError: Если заказ не найден.
        """
        order = await self._repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Заказ {order_id} не найден")
        return order

    async def list_orders(
        self,
        *,
        status: OrderStatus | None = None,
        email: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Order], int]:
        """Возвращает страницу заказов для списка (GET /orders).

        Args:
            status: Фильтр по статусу заказа.
            email: Email покупателя в произвольном регистре.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка заказов и их общего количества.
        """
        normalized_email = email.lower() if email is not None else None
        return await self._repository.list_orders(
            status=status,
            email=normalized_email,
            limit=limit,
            offset=offset,
        )

    async def update_status(
        self, order_id: uuid.UUID, new_status: OrderStatus
    ) -> Order:
        """Переводит заказ в новый статус по заранее заданным правилам.

        Args:
            order_id: Идентификатор заказа.
            new_status: Запрашиваемый новый статус.

        Returns:
            Заказ с обновлённым статусом.
        """
        order = await self.get(order_id)
        current_status = OrderStatus(order.status)

        if not is_transition_allowed(current_status, new_status):
            raise ConflictError(
                f"Переход статуса «{current_status}» → «{new_status}» " "не допускается"
            )

        await self._repository.update_status(order, new_status)
        await self._session.commit()
        return order
