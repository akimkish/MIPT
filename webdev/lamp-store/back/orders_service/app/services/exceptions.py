class NotFoundError(Exception):
    """Запрошенная сущность не найдена."""


class ConflictError(Exception):
    """Запрошенное действие конфликтует с текущим состоянием данных."""


class CheckoutError(Exception):
    """Базовая ошибка оформления заказа.

    Attributes:
        code: Машиночитаемый код для конверта ошибки.
        message: Человекочитаемое сообщение для покупателя.
        details: Дополнительные данные (например, проблемные позиции).
    """

    code = "CHECKOUT_ERROR"
    message = "Заказ не может быть оформлен"

    def __init__(self, details: object = None) -> None:
        """Инициализирует ошибку.

        Args:
            details: Данные для поля details в ответе.
        """
        super().__init__(self.message)
        self.details = details


class DuplicateOrderError(CheckoutError):
    """Повторная отправка формы с тем же idempotency_key (HTTP 409)."""

    code = "DUPLICATE_ORDER"
    message = "Заказ с таким ключом идемпотентности уже создан"


class OutOfStockError(CheckoutError):
    """Не хватает остатка по одной или нескольким позициям (HTTP 409)."""

    code = "INSUFFICIENT_STOCK"
    message = "Недостаточно остатка по некоторым позициям"


class CatalogItemUnavailableError(CheckoutError):
    """Товар снят с продажи или не существует (HTTP 409)."""

    code = "PRODUCT_NOT_AVAILABLE"
    message = "Некоторые товары больше не доступны"


class CheckoutUnavailableError(CheckoutError):
    """Каталог недоступен или ответил ошибкой (HTTP 503).

    """

    code = "CHECKOUT_UNAVAILABLE"
    message = "Сервис заказов временно недоступен, попробуйте позже"
