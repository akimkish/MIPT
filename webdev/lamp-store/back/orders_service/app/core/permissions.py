"""Права, проверяемые по claim `permissions` выпущенного admin_service токена.

ROLE_PERMISSIONS здесь сознательно НЕТ: единственный источник истины о том,
какая роль какие права получает, — `admin_service/app/core/roles.py`. Права
собираются в токен при его выпуске, а этот сервис только сравнивает строки.
Держать вторую копию отображения «роль → права» опасно: она молча разъедется
и никак себя не проявит (ограничение №4 в PROMPT_CONTEXT.md).

ВАЖНО: файл дублируется в трёх сервисах и обязан быть идентичным. Расхождение
константы означает 403 на ровном месте — закрывается тестом на совпадение
множеств значений Permission между сервисами.
"""

import enum


class Permission(enum.StrEnum):
    """Право, которое проверяют products_service и orders_service.

    Значение члена — ровно та строка, которая лежит в claim `permissions`.
    """

    MANAGE_PRODUCTS = "products:write"
    MANAGE_ORDERS = "orders:write"
    MODERATE_REVIEWS = "reviews:moderate"
    MANAGE_CATEGORIES = "categories:write"
    MANAGE_MANUFACTURERS = "manufacturers:write"
    MANAGE_PROMOS = "promos:write"
