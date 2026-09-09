"""Соответствие RoleName и ROLE_PERMISSIONS. Часть раздела 8.

core/roles.py предполагается существующим (упомянут в project_structure
PROMPT_CONTEXT.md, но не реализован на предыдущих шагах) — импорт ниже
зафиксирует расхождение сразу как ImportError, если файла ещё нет.
"""

from app.core.roles import ROLE_PERMISSIONS
from app.models.enums import RoleName


def test_role_permissions_keys_match_role_name_values() -> None:
    """Множество ключей ROLE_PERMISSIONS совпадает с множеством значений RoleName.

    Расхождение здесь — по known_limitations п.4 PROMPT_CONTEXT.md — молча
    лишает администратора прав при выпуске токена, а не падает с ошибкой.
    Этот тест — единственная защита от такого расхождения.
    """
    assert set(ROLE_PERMISSIONS.keys()) == {role.value for role in RoleName}