import enum


class RoleName(enum.StrEnum):

    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    MODERATOR = "moderator"


class AuditAction(enum.StrEnum):

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    ADMIN_CREATED = "admin_created"
    ADMIN_DEACTIVATED = "admin_deactivated"
    ROLE_CHANGED = "role_changed"
