from __future__ import annotations

import logging
from uuid import UUID

from pydantic import ValidationError

from app.clients.base import BaseServiceClient
from app.clients.exceptions import (
    InsufficientStockError,
    ProductNotAvailableError,
    ServiceRejectedError,
    ServiceUnknownStateError,
)
from app.clients.schemas import (
    CartQuote,
    CartQuoteRequest,
    CartQuoteResponse,
    ReleaseRequest,
    ReserveRequest,
    StockItemRequest,
    StockOperationResult,
)
from app.core.config import Settings

logger = logging.getLogger(__name__)

_BASE = "/api/v1/internal/stock"
_RESERVE_URL = f"{_BASE}/reserve"
_RELEASE_URL = f"{_BASE}/release"
_PRICES_URL = f"{_BASE}/prices"


class ProductsClient(BaseServiceClient):
    """Асинхронный клиент products_service."""

    def __init__(self) -> None:
        """Собирает клиент из настроек orders_service.

        X-Internal-Token задаётся один раз на уровне клиента: он одинаков
        для всех internal-запросов, дублировать его в каждом методе незачем.
        """
        super().__init__(
            base_url=Settings.PRODUCTS_SERVICE_URL,
            service_name="products_service",
            connect_timeout=Settings.PRODUCTS_CONNECT_TIMEOUT,
            read_timeout=Settings.PRODUCTS_READ_TIMEOUT,
            headers={"X-Internal-Token": Settings.INTERNAL_API_KEY},
        )

    async def get_prices(self, items: list[StockItemRequest]) -> list[CartQuote]:
        """Считает цены корзины со скидками и отдаёт снимок позиций.

        Args:
            items: Позиции корзины. Количество влияет на скидку через
                promos.min_quantity, поэтому передаётся всегда.

        Returns:
            По одной записи на каждую запрошенную позицию; недоступные
            помечены is_available=False.

        """
        payload = CartQuoteRequest(items=items)
        response = await self.request(
            "POST", _PRICES_URL, json=payload.model_dump(mode="json")
        )
        try:
            return CartQuoteResponse.model_validate(response.json()).items
        except (ValueError, ValidationError) as exc:
            logger.error(
                "products_service returned unparsable prices response: %s", exc
            )
            raise ServiceUnknownStateError(
                "products_service returned unparsable prices response",
                reason="invalid_response_body",
            ) from exc

    async def reserve(
        self, order_id: UUID, items: list[StockItemRequest]
    ) -> StockOperationResult:
        """Списывает остатки по всем позициям заказа.

        Args:
            order_id: Идентификатор заказа, он же ключ идемпотентности.
            items: Позиции заказа.

        Returns:
            Факт операции с флагом already_applied.

        """
        payload = ReserveRequest(order_id=order_id, items=items)
        try:
            response = await self.request(
                "POST", _RESERVE_URL, json=payload.model_dump(mode="json")
            )
        except ServiceRejectedError as exc:
            raise self._map_reserve_rejection(exc) from exc

        try:
            return StockOperationResult.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            # 200 с непонятным телом: списание, скорее всего, СОСТОЯЛОСЬ,
            # поэтому трактуем как неизвестный исход и требуем компенсацию.
            logger.error(
                "products_service returned unparsable reserve response "
                "for order_id=%s: %s",
                order_id,
                exc,
            )
            raise ServiceUnknownStateError(
                "products_service returned unparsable reserve response",
                reason="invalid_response_body",
            ) from exc

    async def release(self, order_id: UUID) -> StockOperationResult:
        """Возвращает остатки, списанные под заказ.

        Args:
            order_id: Идентификатор заказа.

        Returns:
            Факт операции с флагом already_applied.

        """
        payload = ReleaseRequest(order_id=order_id)
        response = await self.request(
            "POST", _RELEASE_URL, json=payload.model_dump(mode="json")
        )
        try:
            return StockOperationResult.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise ServiceUnknownStateError(
                "products_service returned unparsable release response",
                reason="invalid_response_body",
            ) from exc

    @staticmethod
    def _map_reserve_rejection(exc: ServiceRejectedError) -> Exception:
        """Превращает 4xx резерва в конкретное доменное исключение.

        Args:
            exc: Исключение, поднятое базовым клиентом.

        Returns:
            InsufficientStockError, ProductNotAvailableError или исходное
            исключение, если статус не штатный (401/422 — ошибка
            конфигурации, а не бизнес-случай).
        """
        if exc.status_code == 409:
            return InsufficientStockError(
                "Not enough stock", details=exc.body.get("details") or exc.body
            )
        if exc.status_code == 404:
            return ProductNotAvailableError(
                "Product is not available", details=exc.body.get("details")
            )
        return exc
