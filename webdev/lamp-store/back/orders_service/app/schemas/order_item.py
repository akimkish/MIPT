import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemRead(BaseModel):
    """Позиция заказа в ответах API — неизменяемый снимок товара.

    item_id: Идентификатор позиции.
    external_product_id: Идентификатор товара в products_service.
    product_name: Название товара на момент заказа.
    sku: Артикул товара на момент заказа.
    image_url: Ссылка на изображение товара на момент заказа.
    item_quantity: Количество единиц товара в позиции, > 0.
    original_unit_price: Цена за единицу до применения скидки.
    unit_price: Цена за единицу после применения скидки.
    promo_id: Идентификатор применённой акции, если была.
    total_price: Итог по позиции (`unit_price * item_quantity`).
    created_at: Момент создания записи.
    """

    model_config = ConfigDict(from_attributes=True)

    item_id: uuid.UUID
    external_product_id: uuid.UUID
    product_name: str
    sku: str
    image_url: str | None = None
    item_quantity: int = Field(..., gt=0)
    original_unit_price: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    promo_id: uuid.UUID | None = None
    total_price: Decimal = Field(..., ge=0)
    created_at: datetime
