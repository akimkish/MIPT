"""Общие вспомогательные схемы orders_service.

Если этот файл уже существует с этапа schemas — используйте его,
здесь он приведён для самодостаточности слоя api (роуты импортируют
`PaginatedResponse` для списков).
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Страница результатов с общим количеством записей.

    Attributes:
        items: Элементы текущей страницы.
        total: Общее количество записей, подходящих под фильтры
            (без учёта `limit`/`offset`) — нужно фронтенду для пагинации.
    """

    items: list[T]
    total: int