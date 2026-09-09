"""Права по ролям администратора и выпуск списка permissions для JWT.

Единственный источник истины по правам — этот модуль (см.
INTEGRATION_CONTRACT.md → auth_contract: «products/orders сравнивают
строки с константами Permission и о ролях ничего не знают, поэтому
появление новой роли их кода не касается»). Список ролей продублирован
в `RoleName` (models/enums.py) и в CHECK-ограничении таблицы `admins` —
целостность между тремя местами покрывается тестом
`test_role_permissions.py::test_role_permissions_keys_match_role_name_values`.

Строки прав (`Permission`) продублированы в products_service и
orders_service как их собственные `core/permissions.py`
(PROMPT_CONTEXT.md → known_limitations, п.4: «Permission продублирован
в трёх сервисах — расхождение констант молча лишает прав»). Общего
пакета в проекте нет, поэтому синхронизация значений строк между тремя
модулями — ручная дисциплина, а не что-то, что проверяется автоматически
на уровне кода одного сервиса.
"""

import enum

from app.models.enums import RoleName


class Permission(enum.StrEnum):
    """Право, которое проверяют products_service/orders_service по claim JWT.

    Значения — плоские строки вида `"<домен>:<действие>"`, а не иерархия
    объектов: они сравниваются с константами как есть на стороне
    products/orders (`auth_contract`), поэтому формат должен оставаться
    простой строкой без изменений при доработке.
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

Ключи — строки (`RoleName.value`), а не сами члены `RoleName`: это
совпадает с тем, как роль хранится в `admins.role_name` и в claim
`role` токена, и избавляет `get_permissions_for_role` от лишней
конвертации enum → str на каждый вызов.

Роль без записи здесь — это не ошибка Python (обращение по
несуществующему ключу упадёт `KeyError` явно, а не молча вернёт `[]`),
но именно то поведение, которого требует известное ограничение проекта:
«роль без записи в ROLE_PERMISSIONS даст админа с пустыми правами»
(PROMPT_CONTEXT.md → known_limitations, п.4) должно быть невозможно —
выпуск токена должен упасть, а не выдать пустой список.
"""


def get_permissions_for_role(role_name: str) -> list[str]:
    """Возвращает список permission-строк для указанной роли.

    Используется при выпуске access-токена (`core/security.py`) — не
    самой ролью заполняется claim `permissions`, а результатом этой
    функции.

    Args:
        role_name: Значение роли (`admins.role_name`), например
            `"manager"`.

    Returns:
        Список строковых значений прав для этой роли.

    Raises:
        KeyError: Если `role_name` не входит в `ROLE_PERMISSIONS`.
            Осознанно не подставляется пустой список по умолчанию —
            неизвестная роль обязана уронить выпуск токена, а не выдать
            администратора без единого права (см. known_limitations
            п.4 в PROMPT_CONTEXT.md и integration_tests: «Токен с
            role_name, которого нет в ROLE_PERMISSIONS: выпуск токена
            падает в admin_service, а не молча выдаёт пустые
            permissions»).
    """
    return [permission.value for permission in ROLE_PERMISSIONS[role_name]]