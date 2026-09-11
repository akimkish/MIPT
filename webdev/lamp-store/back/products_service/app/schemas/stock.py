from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StockOperationType


class StockItem(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)


class StockReserveRequest(BaseModel):
    order_id: uuid.UUID
    items: list[StockItem] = Field(..., min_length=1)


class StockReleaseRequest(BaseModel):
    order_id: uuid.UUID


class ReservedItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    product_name: str
    sku: str
    image_url: str | None = None
    original_unit_price: Decimal
    unit_price: Decimal
    promo_id: uuid.UUID | None = None


class StockOperationResult(BaseModel):
    order_id: uuid.UUID
    operation: StockOperationType
    already_applied: bool
    items: list[ReservedItemOut] = []
