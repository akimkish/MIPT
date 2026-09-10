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
