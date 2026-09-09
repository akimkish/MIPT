"""Перечисления доменных значений products_service.

Каждый класс соответствует набору допустимых строк из CHECK-ограничения
одноимённой колонки (см. PROMPT_CONTEXT.md → «Перечислимые значения»).
Колонки в ORM объявлены как `String(N)`, а не как SQLAlchemy `Enum`/нативный
ENUM PostgreSQL — эти классы нужны для бизнес-логики и Pydantic-схем
(проверка допустимых значений на уровне Python), а не для маппинга колонки.
"""

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
    """Роль администратора.

    Значения совпадают со строками в CHECK-ограничении таблицы `admins`
    и с ключами словаря `ROLE_PERMISSIONS` (core/roles.py, следующий шаг).
    Список ролей фиксирован: добавление новой роли — это правка данного
    перечисления, миграция CHECK-ограничения и правка `ROLE_PERMISSIONS`
    одним коммитом.
    """

    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    MODERATOR = "moderator"
