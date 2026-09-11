import uuid


class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class DomainValidationError(DomainError):
    pass


class InsufficientStockError(DomainError):
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

class ProductNotAvailableError(NotFoundError):
    """Товар не найден или снят с продажи (`is_active = false`).
 
    Attributes:
        product_id: Идентификатор недоступного товара, если известен.
    """
 
    def __init__(self, message: str, product_id: uuid.UUID | None = None) -> None:
        """
        Args:
            message: Текст причины для лога и поля `message` ответа.
            product_id: Идентификатор недоступного товара.
        """
        super().__init__(message)
        self.product_id = product_id