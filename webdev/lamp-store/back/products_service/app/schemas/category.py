"""Pydantic-схемы категории товаров."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Поля категории, общие для создания и чтения.

    Attributes:
        name: Название категории. Уникальность без учёта регистра
            проверяется в репозитории (индекс по `lower(name)` в БД),
            здесь — только базовая валидация длины.
        description: Необязательное описание.
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None)


class CategoryCreate(CategoryBase):
    """Данные для создания категории. Полностью повторяет `CategoryBase`."""


class CategoryUpdate(BaseModel):
    """Данные для частичного обновления категории (PATCH).

    Все поля необязательны: в запросе передаются только те, что меняются.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class CategoryRead(CategoryBase):
    """Категория в ответах API."""

    model_config = ConfigDict(from_attributes=True)

    category_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
