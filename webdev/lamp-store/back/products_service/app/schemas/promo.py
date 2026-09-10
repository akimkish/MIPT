import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import DiscountType


class PromoBase(BaseModel):
    promo_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    discount_type: DiscountType
    discount: Decimal = Field(..., gt=0)
    product_id: uuid.UUID
    min_quantity: int = Field(default=1, ge=1)
    valid_from: datetime
    valid_to: datetime

    @model_validator(mode="after")
    def check_discount_bounds(self) -> "PromoBase":

        if self.discount_type == DiscountType.PERCENT and self.discount > 100:
            raise ValueError("Процентная скидка не может превышать 100")
        return self

    @model_validator(mode="after")
    def check_dates_order(self) -> "PromoBase":

        if self.valid_from >= self.valid_to:
            raise ValueError("valid_from должен быть раньше valid_to")
        return self


class PromoCreate(PromoBase):
    pass


class PromoUpdate(BaseModel):

    promo_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    discount_type: DiscountType | None = None
    discount: Decimal | None = Field(default=None, gt=0)
    min_quantity: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None


class PromoRead(PromoBase):

    model_config = ConfigDict(from_attributes=True)

    promo_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
