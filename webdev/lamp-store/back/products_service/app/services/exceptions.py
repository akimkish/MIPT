"""Доменные исключения сервисного слоя.

Сервисы не знают про HTTP и не поднимают `HTTPException` — они бросают
эти исключения, а слой `api` переводит их в коды ответа (404/409/422).
Так бизнес-логику можно тестировать без TestClient и переиспользовать
из internal-эндпоинтов, где формат ошибок другой.
"""

import uuid


class DomainError(Exception):
    """Базовое исключение доменной логики сервиса."""


class NotFoundError(DomainError):
    """Запрошенная сущность не найдена (отображается в HTTP 404)."""


class ConflictError(DomainError):
    """Нарушение уникальности или состояния (отображается в HTTP 409)."""


class DomainValidationError(DomainError):
    """Некорректные данные с точки зрения бизнес-правил (HTTP 422).

    Отличается от ошибки валидации Pydantic тем, что проверка требует
    данных из БД или уже сохранённых значений (например, корректность
    дат акции при частичном обновлении).
    """


class InsufficientStockError(DomainError):
    """Остатка товара не хватает для списания (отображается в HTTP 409).

    Attributes:
        product_id: Товар, на котором операция не прошла.
        requested: Запрошенное количество.
        available: Фактический остаток на момент проверки; `None`, если
            товар вовсе не найден.
    """

    def __init__(
        self,
        product_id: uuid.UUID,
        requested: int,
        available: int | None,
    ) -> None:
        """Инициализирует исключение.

        Args:
            product_id: Идентификатор товара.
            requested: Запрошенное количество.
            available: Доступный остаток или `None`, если товар не найден.
        """
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Недостаточно остатка по товару {product_id}: "
            f"запрошено {requested}, доступно {available}"
        )