from enum import StrEnum
import enum

class OrderStatus(StrEnum):
    PENDING = "pending"
    FAILED = "failed"
    NEW = "new"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RoleName(enum.StrEnum):

    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    MODERATOR = "moderator"