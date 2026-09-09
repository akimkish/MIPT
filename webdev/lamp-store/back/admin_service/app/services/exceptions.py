"""Исключения сервисного слоя admin_service.

Единая иерархия, которую api-слой транслирует в HTTP через обработчик
исключений FastAPI (единый конверт ошибки {"code","message","details"} —
см. INTEGRATION_CONTRACT.md). Сервисы ничего не знают про HTTP-коды.
"""


class ServiceError(Exception):
    """Базовое исключение сервисного слоя."""


class NotFoundError(ServiceError):
    """Запрашиваемая сущность не найдена."""


class ConflictError(ServiceError):
    """Действие конфликтует с текущим состоянием данных (например, email занят)."""


class AuthenticationError(ServiceError):
    """Неверные учётные данные либо невалидный/просроченный токен."""


class AccountLockedError(ServiceError):
    """Учётная запись временно заблокирована после серии неудачных входов."""


class InactiveAccountError(ServiceError):
    """Учётная запись деактивирована."""


class PermissionDeniedError(ServiceError):
    """Действие требует роли, которой нет у текущего администратора."""
