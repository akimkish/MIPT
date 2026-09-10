import enum

from app.models.enums import RoleName


class Permission(enum.StrEnum):

    MANAGE_PRODUCTS = "products:write"
    MANAGE_ORDERS = "orders:write"
    MODERATE_REVIEWS = "reviews:moderate"
    MANAGE_CATEGORIES = "categories:write"
    MANAGE_MANUFACTURERS = "manufacturers:write"
    MANAGE_PROMOS = "promos:write"


ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    RoleName.SUPERADMIN.value: [
        Permission.MANAGE_PRODUCTS,
        Permission.MANAGE_ORDERS,
        Permission.MODERATE_REVIEWS,
        Permission.MANAGE_CATEGORIES,
        Permission.MANAGE_MANUFACTURERS,
        Permission.MANAGE_PROMOS,
    ],
    RoleName.MANAGER.value: [
        Permission.MANAGE_PRODUCTS,
        Permission.MANAGE_ORDERS,
        Permission.MANAGE_CATEGORIES,
        Permission.MANAGE_PROMOS,
    ],
    RoleName.MODERATOR.value: [
        Permission.MODERATE_REVIEWS,
    ],
}


def get_permissions_for_role(role_name: str) -> list[str]:

    return [permission.value for permission in ROLE_PERMISSIONS[role_name]]
