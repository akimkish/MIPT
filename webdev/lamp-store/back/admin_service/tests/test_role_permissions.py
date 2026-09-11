from app.core.roles import ROLE_PERMISSIONS
from app.models.enums import RoleName


def test_role_permissions_keys_match_role_name_values() -> None:

    assert set(ROLE_PERMISSIONS.keys()) == {role.value for role in RoleName}
