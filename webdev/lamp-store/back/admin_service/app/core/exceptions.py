from dataclasses import dataclass

from fastapi import status

from app.services.exceptions import (
    AccountLockedError,
    AuthenticationError,
    ConflictError,
    InactiveAccountError,
    NotFoundError,
    PermissionDeniedError,
    ServiceError,
)


@dataclass(frozen=True)
class ErrorMapping:
    """Соответствие типа исключения HTTP-статусу и машинному коду ошибки.

    Attributes:
        status_code: HTTP-статус ответа.
        code: Машиночитаемый код для тела ошибки.
    """

    status_code: int
    code: str


EXCEPTION_MAPPING: dict[type[ServiceError], ErrorMapping] = {
    NotFoundError: ErrorMapping(status.HTTP_404_NOT_FOUND, "NOT_FOUND"),
    ConflictError: ErrorMapping(status.HTTP_409_CONFLICT, "CONFLICT"),
    AuthenticationError: ErrorMapping(
        status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_FAILED"
    ),
    AccountLockedError: ErrorMapping(status.HTTP_423_LOCKED, "ACCOUNT_LOCKED"),
    InactiveAccountError: ErrorMapping(status.HTTP_403_FORBIDDEN, "ACCOUNT_INACTIVE"),
    PermissionDeniedError: ErrorMapping(status.HTTP_403_FORBIDDEN, "PERMISSION_DENIED"),
    ServiceError: ErrorMapping(status.HTTP_400_BAD_REQUEST, "SERVICE_ERROR"),
}


def resolve_error_mapping(exc: ServiceError) -> ErrorMapping:
    """Находит наиболее специфичное сопоставление для исключения.

    Args:
        exc: Пойманное исключение сервисного слоя.

    Returns:
        Сопоставление HTTP-статуса и кода ошибки.
    """
    for exc_type in type(exc).__mro__:
        if exc_type in EXCEPTION_MAPPING:
            return EXCEPTION_MAPPING[exc_type]
    return EXCEPTION_MAPPING[ServiceError]
