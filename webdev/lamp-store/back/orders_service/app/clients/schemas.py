from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# --- запросы -----------------------------------------------------------------


class StockItemRequest(BaseModel):
    """Позиция заказа: товар и количество."""

    model_config = ConfigDict(frozen=True)

    product_id: UUID
    quantity: int = Field(gt=0)


class ReserveRequest(BaseModel):
    """Тело POST /api/v1/internal/stock/reserve."""

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    items: list[StockItemRequest] = Field(min_length=1)


class ReleaseRequest(BaseModel):
    """Тело POST /api/v1/internal/stock/release.

    Количества не передаются осознанно: products_service берёт их из
    payload записи 'reserve'. Если бы количества присылал orders_service,
    повторный вызов вернул бы остаток дважды.
    """

    model_config = ConfigDict(frozen=True)

    order_id: UUID


class CartQuoteRequest(BaseModel):
    """Тело POST /api/v1/internal/stock/prices."""

    model_config = ConfigDict(frozen=True)

    items: list[StockItemRequest] = Field(min_length=1)


# --- ответы ------------------------------------------------------------------


class StockOperationResult(BaseModel):
    """Ответ 200 на reserve и release.

    Attributes:
        order_id: Заказ, по которому выполнена операция.
        operation: 'reserve' или 'release'.
        already_applied: True, если операция выполнялась ранее и ничего
            не изменилось.
    """

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    operation: str
    already_applied: bool


class CartQuote(BaseModel):
    """Снимок одной позиции корзины.

    Именно эти значения копируются в order_items и больше никогда
    не меняются. У недоступного товара заполнены только `product_id`
    и `is_available`.
    """

    model_config = ConfigDict(frozen=True)

    product_id: UUID
    is_available: bool
    product_name: str | None = None
    sku: str | None = None
    image_url: str | None = None
    quantity_available: int | None = None
    original_unit_price: Decimal | None = None
    unit_price: Decimal | None = None
    promo_id: UUID | None = None


class CartQuoteResponse(BaseModel):
    """Ответ 200 на расчёт цен корзины."""

    model_config = ConfigDict(frozen=True)

    items: list[CartQuote]
