import uuid
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CartItemIn(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CartQuoteRequest(BaseModel):

    model_config = ConfigDict(frozen=True)

    items: list[CartItemIn] = Field(min_length=1)

    @model_validator(mode="after")
    def check_unique_products(self) -> Self:

        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Товар не может встречаться в корзине дважды")
        return self


class CartQuoteOut(BaseModel):

    model_config = ConfigDict(frozen=True)

    product_id: uuid.UUID
    is_available: bool
    product_name: str | None = None
    sku: str | None = None
    image_url: str | None = None
    quantity_available: int | None = None
    original_unit_price: Decimal | None = None
    unit_price: Decimal | None = None
    promo_id: uuid.UUID | None = None


class CartQuoteListOut(BaseModel):

    model_config = ConfigDict(frozen=True)

    items: list[CartQuoteOut]
