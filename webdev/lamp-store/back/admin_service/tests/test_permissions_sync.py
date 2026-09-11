from app.core.permissions import Permission  # admin_service: from app.core.roles

EXPECTED_PERMISSIONS = {
    "products:write",
    "orders:write",
    "reviews:moderate",
    "categories:write",
    "manufacturers:write",
    "promos:write",
}


def test_permission_values_match_contract() -> None:
    """Множество прав сервиса совпадает с общим для проекта списком."""
    assert {permission.value for permission in Permission} == EXPECTED_PERMISSIONS


def test_permission_values_are_unique() -> None:
    """У разных членов Permission не может быть одинаковых значений."""
    values = [permission.value for permission in Permission]
    assert len(values) == len(set(values))
