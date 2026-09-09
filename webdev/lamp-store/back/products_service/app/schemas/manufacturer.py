"""Pydantic-схемы производителя товаров."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ManufacturerBase(BaseModel):
    """Поля производителя, общие для создания и чтения.

    Attributes:
        name: Название производителя. Уникальность без учёта регистра
            проверяется в репозитории (см. `CategoryBase.name`).
        description: Необязательное описание.
        logo_url: Необязательная ссылка на логотип.
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None)
    logo_url: str | None = Field(default=None, max_length=500)


class ManufacturerCreate(ManufacturerBase):
    """Данные для создания производителя."""


class ManufacturerUpdate(BaseModel):
    """Данные для частичного обновления производителя (PATCH)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ManufacturerRead(ManufacturerBase):
    """Производитель в ответах API."""

    model_config = ConfigDict(from_attributes=True)

    manufacturer_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
