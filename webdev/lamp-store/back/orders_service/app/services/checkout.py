from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.clients.exceptions import (
    InsufficientStockError,
    ProductNotAvailableError,
    ServiceRejectedError,
    ServiceUnavailableError,
    ServiceUnknownStateError,
)
from app.clients.products import ProductsClient
from app.clients.schemas import CartQuote, StockItemRequest
from app.models.enums import OrderStatus
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate
from app.services.exceptions import (
    CatalogItemUnavailableError,
    CheckoutUnavailableError,
    DuplicateOrderError,
    OutOfStockError,
)

logger = logging.getLogger(__name__)


class CheckoutService:
    def __init__(self, repository: OrderRepository, products: ProductsClient) -> None:
        self._repository = repository
        self._products = products

    async def create_order(self, payload: OrderCreate) -> Order:
        """Оформляет заказ целиком.

        Args:
            payload: Данные покупателя, позиции корзины и idempotency_key.

        Returns:
            Созданный заказ в статусе 'new' вместе с позициями.

        """
        items = [
            StockItemRequest(product_id=item.product_id, quantity=item.quantity)
            for item in payload.items
        ]

        order = await self._create_pending(payload)
        quotes = await self._quote(order.order_id, items)
        await self._reserve(order.order_id, items)
        return await self._persist(order.order_id, items, quotes)

    async def _create_pending(self, payload: OrderCreate) -> Order:
        """Создаёт заказ-заглушку в статусе 'pending'.

        Args:
            payload: Данные заказа.

        Returns:
            Сохранённый заказ в статусе 'pending'.
        """
        try:
            return await self._repository.create_pending(payload)
        except IntegrityError as exc:
            logger.info(
                "Duplicate idempotency_key=%s rejected", payload.idempotency_key
            )
            raise DuplicateOrderError() from exc
        except SQLAlchemyError as exc:
            logger.exception("Failed to create pending order: %s", exc)
            raise CheckoutUnavailableError() from exc

    async def _quote(
        self, order_id: UUID, items: list[StockItemRequest]
    ) -> dict[UUID, CartQuote]:
        """Получает цены и снимок позиций до изменения остатков.

        Args:
            order_id: Идентификатор заказа (для логов и смены статуса).
            items: Позиции заказа.

        Returns:
            Снимок по каждому товару.
        """
        try:
            quotes = await self._products.get_prices(items)
        except (
            ServiceUnavailableError,
            ServiceUnknownStateError,
            ServiceRejectedError,
        ) as exc:
            logger.warning(
                "Price quote failed for order_id=%s (%s)", order_id, exc.reason
            )
            await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        by_id = {quote.product_id: quote for quote in quotes}
        unavailable = [
            str(item.product_id)
            for item in items
            if item.product_id not in by_id or not by_id[item.product_id].is_available
        ]
        if unavailable:
            logger.info(
                "Order %s rejected: products unavailable %s", order_id, unavailable
            )
            await self._mark_failed(order_id)
            raise CatalogItemUnavailableError(details={"product_ids": unavailable})

        return by_id

    async def _reserve(self, order_id: UUID, items: list[StockItemRequest]) -> None:
        """Списывает остатки в products_service.

        Args:
            order_id: Идентификатор заказа, он же ключ идемпотентности.
            items: Позиции заказа.
        """
        try:
            result = await self._products.reserve(order_id, items)

        except ServiceUnavailableError as exc:
            logger.warning(
                "Reserve not sent for order_id=%s (%s)", order_id, exc.reason
            )
            await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        except ServiceUnknownStateError as exc:
            logger.error(
                "Reserve outcome unknown for order_id=%s (%s), compensating",
                order_id,
                exc.reason,
            )
            if await self._release_best_effort(order_id):
                await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        except InsufficientStockError as exc:
            await self._mark_failed(order_id)
            raise OutOfStockError(details=exc.details) from exc

        except ProductNotAvailableError as exc:
            await self._mark_failed(order_id)
            raise CatalogItemUnavailableError(details=exc.details) from exc

        except ServiceRejectedError as exc:

            logger.error(
                "Reserve rejected for order_id=%s: HTTP %s code=%s",
                order_id,
                exc.status_code,
                exc.code,
            )
            await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

        if result.already_applied:
            logger.warning("Reserve for order_id=%s reported already_applied", order_id)

    async def _persist(
        self,
        order_id: UUID,
        items: list[StockItemRequest],
        quotes: dict[UUID, CartQuote],
    ) -> Order:
        """Сохраняет позиции заказа и переводит его в статус 'new'.

        Args:
            order_id: Идентификатор заказа.
            items: Исходные позиции (источник количеств).
            quotes: Снимок из products_service (источник цен и названий).

        Returns:
            Заказ в статусе 'new'.
        """
        lines = self._build_lines(items, quotes)
        try:
            return await self._repository.complete(order_id, lines)
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to persist items for order_id=%s, compensating", order_id
            )
            if await self._release_best_effort(order_id):
                await self._mark_failed(order_id)
            raise CheckoutUnavailableError() from exc

    @staticmethod
    def _build_lines(
        items: list[StockItemRequest], quotes: dict[UUID, CartQuote]
    ) -> list[dict[str, object]]:
        """Склеивает количества из корзины с ценами из снимка.

        Args:
            items: Позиции корзины.
            quotes: Снимок из products_service.

        Returns:
            Данные для INSERT в order_items.
        """
        lines: list[dict[str, object]] = []
        for item in items:
            quote = quotes[item.product_id]
            unit_price: Decimal = quote.unit_price
            lines.append(
                {
                    "external_product_id": quote.product_id,
                    "product_name": quote.product_name,
                    "sku": quote.sku,
                    "image_url": quote.image_url,
                    "item_quantity": item.quantity,
                    "original_unit_price": quote.original_unit_price,
                    "unit_price": unit_price,
                    "promo_id": quote.promo_id,
                    # Округление уже выполнено в products_service на уровне
                    # unit_price; здесь только умножение, иначе копейки поедут.
                    "total_price": unit_price * item.quantity,
                }
            )
        return lines

    async def _release_best_effort(self, order_id: UUID) -> bool:
        """Пытается вернуть остатки. Одна попытка, исключения не пробрасывает.

        Args:
            order_id: Идентификатор заказа.

        Returns:
            True, если компенсация прошла; False, если заказ остался
            в статусе 'pending' и требует ручного разбора.
        """
        try:
            await self._products.release(order_id)
        except Exception as exc:  # noqa: BLE001 - компенсация не должна падать
            logger.error(
                "MANUAL ACTION REQUIRED: release failed for order_id=%s (%s), "
                "order left in 'pending'",
                order_id,
                exc,
            )
            return False
        logger.info("Stock released for order_id=%s", order_id)
        return True

    async def _mark_failed(self, order_id: UUID) -> None:
        """Переводит заказ в 'failed' отдельной транзакцией.

        Args:
            order_id: Идентификатор заказа.
        """
        try:
            await self._repository.set_status(order_id, OrderStatus.FAILED)
        except SQLAlchemyError as exc:
            logger.error("Failed to mark order_id=%s as failed: %s", order_id, exc)
