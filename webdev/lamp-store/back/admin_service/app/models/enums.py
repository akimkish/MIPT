"""Общие перечисления admin_service."""

import enum


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


class AuditAction(enum.StrEnum):
    """Тип события в журнале аудита admin_service."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    ADMIN_CREATED = "admin_created"
    ADMIN_DEACTIVATED = "admin_deactivated"
    ROLE_CHANGED = "role_changed"