import enum

from app.models.enums import RoleName


class Permission(enum.StrEnum):
    """Право, которое проверяют products_service/orders_service по claim JWT.
    """

    MANAGE_PRODUCTS = "products:write"
    MANAGE_ORDERS = "orders:write"
    MODERATE_REVIEWS = "reviews:moderate"


ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    RoleName.SUPERADMIN.value: [
        Permission.MANAGE_PRODUCTS,
        Permission.MANAGE_ORDERS,
        Permission.MODERATE_REVIEWS,
    ],
    RoleName.MANAGER.value: [
        Permission.MANAGE_PRODUCTS,
        Permission.MANAGE_ORDERS,
    ],
    RoleName.MODERATOR.value: [
        Permission.MODERATE_REVIEWS,
    ],
}
"""Права, выдаваемые каждой ролью при выпуске токена.

"""


def get_permissions_for_role(role_name: str) -> list[str]:
    """Возвращает список permission-строк для указанной роли.

    Args:
        role_name: Значение роли (`admins.role_name`), например
            `"manager"`.

    Returns:
        Список строковых значений прав для этой роли.

    """
    return [permission.value for permission in ROLE_PERMISSIONS[role_name]]