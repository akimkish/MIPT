from __future__ import annotations

from typing import Any


class ProductsClientError(Exception):
    """Базовая ошибка обращения к products_service.

    Attributes:
        reason: Короткая машиночитаемая причина для логов.
        request_sent: Дошёл ли запрос до сервиса.
    """

    request_sent: bool = False

    def __init__(self, message: str, *, reason: str) -> None:
        """Инициализирует исключение.

        Args:
            message: Человекочитаемое описание для лога.
            reason: Короткий код причины (например, "connect_timeout").
        """
        super().__init__(message)
        self.reason = reason


class ServiceUnavailableError(ProductsClientError):
    """Соединение не установлено: ConnectError или ConnectTimeout.

    Резерв гарантированно не состоялся, компенсация не нужна.
    """

    request_sent = False


class ServiceUnknownStateError(ProductsClientError):
    """Запрос ушёл, но результат неизвестен: ReadTimeout, 5xx, битый ответ.

    Резерв мог закоммититься. Обязательна компенсация release.
    """

    request_sent = True


class ServiceRejectedError(ProductsClientError):
    """Сервис ответил 4xx, кроме штатных 409/404.
        Attributes:
        status_code: HTTP-статус ответа.
        code: Значение поля "code" из конверта ошибки, если оно было.
        body: Разобранное тело ответа целиком (нужно для details у 409).
    """

    request_sent = True

    def __init__(
        self,
        message: str,
        *,
        reason: str,
        status_code: int,
        code: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        """Инициализирует исключение.

        Args:
            message: Описание для лога.
            reason: Короткий код причины.
            status_code: HTTP-статус ответа products_service.
            code: Машиночитаемый код ошибки из тела ответа.
            body: Тело ответа в виде словаря (пустой, если тело не JSON).
        """
        super().__init__(message, reason=reason)
        self.status_code = status_code
        self.code = code
        self.body = body or {}


class InsufficientStockError(ProductsClientError):
    """409 от reserve: не хватает остатка по одной из позиций.

    Attributes:
        details: Детали из ответа products_service — пробрасываются
            покупателю в поле details. Формат не фиксируется: конверт
            ошибки чужого сервиса может измениться, и клиент не должен
            из-за этого падать.
    """

    request_sent = True

    def __init__(self, message: str, *, details: Any = None) -> None:
        """Инициализирует исключение.

        Args:
            message: Описание для лога.
            details: Детали нехватки остатка из ответа сервиса.
        """
        super().__init__(message, reason="insufficient_stock")
        self.details = details


class ProductNotAvailableError(ProductsClientError):
    """404 PRODUCT_NOT_AVAILABLE: товара нет или он снят с продажи.

    Attributes:
        details: Тело ответа products_service (какие именно товары).
    """

    request_sent = True

    def __init__(self, message: str, *, details: Any = None) -> None:
        """Инициализирует исключение.

        Args:
            message: Описание для лога.
            details: Детали из ответа products_service.
        """
        super().__init__(message, reason="product_not_available")
        self.details = details