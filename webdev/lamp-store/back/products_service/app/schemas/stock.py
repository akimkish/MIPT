import uuid

from pydantic import BaseModel, Field


class StockItem(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)


class StockReserveRequest(BaseModel):
    order_id: uuid.UUID
    items: list[StockItem] = Field(..., min_length=1)


class StockReleaseRequest(BaseModel):
    order_id: uuid.UUID


class StockOperationResult(BaseModel):
    order_id: uuid.UUID
    operation: str
    already_applied: bool
