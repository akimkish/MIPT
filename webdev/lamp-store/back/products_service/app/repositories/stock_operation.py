"""Репозиторий журнала складских операций (идемпотентность reserve/release)."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StockOperationType
from app.models.stock_operation import StockOperation


class StockOperationRepository:
    """Доступ к журналу операций списания и возврата остатка."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def get(
        self, order_id: uuid.UUID, operation: StockOperationType
    ) -> StockOperation | None:
        """Возвращает запись об уже выполненной операции по заказу.

        Args:
            order_id: Идентификатор заказа из orders_service.
            operation: Тип операции (`reserve` или `release`).

        Returns:
            Запись журнала или `None`, если операция ещё не выполнялась.
        """
        return await self._session.get(StockOperation, (order_id, operation.value))

    async def create(
        self,
        order_id: uuid.UUID,
        operation: StockOperationType,
        payload: dict[str, Any] | None = None,
    ) -> StockOperation:
        """Записывает факт выполнения операции в журнал.

        Вставка выполняется в той же транзакции, что и сам `UPDATE`
        остатка: либо в БД окажется и изменённое количество, и запись
        журнала, либо ничего — иначе идемпотентность сломается.

        Args:
            order_id: Идентификатор заказа из orders_service.
            operation: Тип операции (`reserve` или `release`).
            payload: Снимок позиций заказа. Для `reserve` обязателен —
                из него берутся количества при последующем `release`.

        Returns:
            Созданную запись журнала.
        """
        record = StockOperation(
            order_id=order_id,
            operation=operation.value,
            payload=payload,
        )
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record
