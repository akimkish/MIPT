"""Общие Pydantic-схемы, переиспользуемые в разных роутерах."""

from typing import Generic, TypeVar

from pydantic import BaseModel

ItemT = TypeVar("ItemT")


class PaginatedResponse(BaseModel, Generic[ItemT]):
    """Постраничный ответ списковых эндпоинтов.

    Attributes:
        items: Элементы текущей страницы.
        total: Общее количество элементов, подходящих под фильтры
            (без учёта `limit`/`offset`).
    """

    items: list[ItemT]
    total: int


class ErrorResponse(BaseModel):
    """Единый конверт ошибки API (INTEGRATION_CONTRACT.md → service_integration).

    Attributes:
        code: Машиночитаемый код ошибки (например, `"NOT_FOUND"`).
        message: Сообщение для отображения или логирования.
        details: Произвольные дополнительные данные об ошибке;
            `None`, если добавить нечего.
    """

    code: str
    message: str
    details: dict | list | None = None