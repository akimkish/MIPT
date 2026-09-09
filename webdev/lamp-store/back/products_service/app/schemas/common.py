"""Общие компоненты Pydantic-схем: пагинация и обёртка списка."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Параметры пагинации для списковых эндпоинтов каталога.

    Attributes:
        limit: Размер страницы, от 1 до 100.
        offset: Смещение от начала выборки, >= 0.
    """

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Обёртка над списком элементов с общим количеством для пагинации.

    Attributes:
        items: Элементы текущей страницы.
        total: Общее количество элементов без учёта `limit`/`offset`
            (нужно фронтенду для отрисовки пагинатора).
    """

    items: list[T]
    total: int = Field(..., ge=0)
