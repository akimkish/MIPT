import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SocketType
from app.schemas.category import CategoryRead
from app.schemas.manufacturer import ManufacturerRead


class ProductBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=32)
    category_id: uuid.UUID
    manufacturer_id: uuid.UUID
    price: Decimal = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    description: str | None = Field(default=None)
    power_watts: Decimal = Field(..., gt=0)
    socket_type: SocketType
    color_temperature_k: int = Field(..., ge=1000, le=10000)
    image_url: str | None = Field(default=None, max_length=500)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=32)
    category_id: uuid.UUID | None = None
    manufacturer_id: uuid.UUID | None = None
    price: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    power_watts: Decimal | None = Field(default=None, gt=0)
    socket_type: SocketType | None = None
    color_temperature_k: int | None = Field(default=None, ge=1000, le=10000)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductWithRelations(ProductRead):
    category: CategoryRead
    manufacturer: ManufacturerRead


class ProductCatalogItem(ProductRead):
    display_price: Decimal = Field(..., ge=0)
    bulk_discount_hint: str | None = Field(default=None)


class ProductDetail(ProductCatalogItem):

    category: CategoryRead
    manufacturer: ManufacturerRead
    average_rating: float | None = Field(default=None)
