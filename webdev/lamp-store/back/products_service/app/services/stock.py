import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StockOperationType
from app.repositories.product import ProductRepository
from app.repositories.stock_operation import StockOperationRepository
from app.schemas.stock import StockItem, StockOperationResult
from app.services.exceptions import (
    ConflictError,
    DomainValidationError,
    InsufficientStockError,
)


class StockService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._products = ProductRepository(session)
        self._operations = StockOperationRepository(session)

    async def reserve(
        self, order_id: uuid.UUID, items: Sequence[StockItem]
    ) -> StockOperationResult:
        """Списывает остатки по всем позициям заказа в одной транзакции.

        Args:
            order_id: Идентификатор заказа из orders_service; служит
                ключом идемпотентности.
            items: Позиции заказа, каждая с положительным количеством.

        Returns:
            Результат операции; `already_applied=True`, если списание
            по этому заказу уже выполнялось ранее.

        """
        self._validate_items(items)

        existing = await self._operations.get(order_id, StockOperationType.RESERVE)
        if existing is not None:
            return StockOperationResult(
                order_id=order_id,
                operation=StockOperationType.RESERVE.value,
                already_applied=True,
            )

        ordered_items = sorted(items, key=lambda item: str(item.product_id))

        try:
            for item in ordered_items:
                updated = await self._products.decrease_quantity(
                    item.product_id, item.quantity
                )
                if not updated:
                    product = await self._products.get_by_id(item.product_id)
                    raise InsufficientStockError(
                        product_id=item.product_id,
                        requested=item.quantity,
                        available=product.quantity if product else None,
                    )

            await self._operations.create(
                order_id=order_id,
                operation=StockOperationType.RESERVE,
                payload=self._build_payload(ordered_items),
            )
            await self._session.commit()
        except IntegrityError:

            await self._session.rollback()
            return StockOperationResult(
                order_id=order_id,
                operation=StockOperationType.RESERVE.value,
                already_applied=True,
            )
        except Exception:
            await self._session.rollback()
            raise

        return StockOperationResult(
            order_id=order_id,
            operation=StockOperationType.RESERVE.value,
            already_applied=False,
        )

    async def release(self, order_id: uuid.UUID) -> StockOperationResult:
        """Возвращает на склад остатки, списанные ранее под заказ.

        Args:
            order_id: Идентификатор заказа из orders_service.

        Returns:
            Результат операции; `already_applied=True`, если возврат по
            этому заказу уже выполнялся.

        """
        existing = await self._operations.get(order_id, StockOperationType.RELEASE)
        if existing is not None:
            return StockOperationResult(
                order_id=order_id,
                operation=StockOperationType.RELEASE.value,
                already_applied=True,
            )

        reserve_record = await self._operations.get(
            order_id, StockOperationType.RESERVE
        )
        if reserve_record is None or not reserve_record.payload:

            return StockOperationResult(
                order_id=order_id,
                operation=StockOperationType.RELEASE.value,
                already_applied=True,
            )

        items = reserve_record.payload["items"]

        try:
            for item in items:
                await self._products.increase_quantity(
                    uuid.UUID(item["product_id"]), int(item["quantity"])
                )
            await self._operations.create(
                order_id=order_id,
                operation=StockOperationType.RELEASE,
                payload=reserve_record.payload,
            )
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            return StockOperationResult(
                order_id=order_id,
                operation=StockOperationType.RELEASE.value,
                already_applied=True,
            )
        except Exception:
            await self._session.rollback()
            raise

        return StockOperationResult(
            order_id=order_id,
            operation=StockOperationType.RELEASE.value,
            already_applied=False,
        )

    @staticmethod
    def _validate_items(items: Sequence[StockItem]) -> None:
        """Проверяет корректность набора позиций до обращения к БД.

        Args:
            items: Позиции заказа.


        """
        if not items:
            raise DomainValidationError("Список позиций не может быть пустым")

        product_ids = [item.product_id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise DomainValidationError("Товар не может встречаться в заказе дважды")

    @staticmethod
    def _build_payload(items: Sequence[StockItem]) -> dict[str, Any]:
        """Готовит снимок позиций для записи в JSONB-поле журнала.

        Args:
            items: Позиции заказа.

        Returns:
            Словарь вида `{"items": [{"product_id": ..., "quantity": ...}]}`
            со строковыми идентификаторами (UUID не сериализуется в JSON
            напрямую).
        """
        return {
            "items": [
                {"product_id": str(item.product_id), "quantity": item.quantity}
                for item in items
            ]
        }
