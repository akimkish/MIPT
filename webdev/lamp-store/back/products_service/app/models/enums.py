from enum import StrEnum
import enum


class SocketType(StrEnum):
    """Типы цоколя лампы, допустимые для `products.socket_type`."""

    E14 = "E14"
    E27 = "E27"
    E40 = "E40"
    G4 = "G4"
    G9 = "G9"
    G13 = "G13"
    GU10 = "GU10"
    GU5_3 = "GU5.3"


class DiscountType(StrEnum):
    """Тип скидки акции: процент от цены или фиксированная сумма."""

    PERCENT = "percent"
    FIXED = "fixed"


class StockOperationType(StrEnum):
    """Тип складской операции в журнале идемпотентности."""

    RESERVE = "reserve"
    RELEASE = "release"


class RoleName(enum.StrEnum):
    """Роль администратора."""

    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    MODERATOR = "moderator"
