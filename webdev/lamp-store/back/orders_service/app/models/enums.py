"""Перечисления, используемые в моделях orders_service."""

from enum import StrEnum
import enum

class OrderStatus(StrEnum):
    """Статус заказа.

    Значения совпадают со строками в БД (CHECK-ограничение на
    `orders.status`), поэтому `values_callable` в mapped_column не нужен.
    """

    PENDING = "pending"
    FAILED = "failed"
    NEW = "new"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

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