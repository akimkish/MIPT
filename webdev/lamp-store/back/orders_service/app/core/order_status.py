"""Правила допустимых переходов статуса заказа.

Единственный источник истины для проверки, можно ли перевести заказ
из одного статуса в другой — по аналогии с `ROLE_PERMISSIONS` в
admin_service (там тоже словарь-константа, а не что-то в БД).
"""

from app.models.enums import OrderStatus

ORDER_STATUS_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    # pending/failed выставляются самим процессом оформления заказа
    # (Этап 7: пока идёт списание остатка в products_service), а не
    # админом через узкий эндпоинт смены статуса — поэтому у них нет
    # исходящих переходов, доступных отсюда.
    OrderStatus.PENDING: frozenset(),
    OrderStatus.FAILED: frozenset(),
    OrderStatus.NEW: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),
    OrderStatus.PAID: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.COMPLETED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}
"""Граф переходов: new → paid → shipped → completed,
с возможностью отмены (`cancelled`) из `new` или `paid`.
После отгрузки отмена уже не имеет смысла для интернет-магазина
лампочек — товар физически едет к покупателю."""


def is_transition_allowed(current: OrderStatus, target: OrderStatus) -> bool:
    """Проверяет, допустим ли переход между статусами.

    Args:
        current: Текущий статус заказа.
        target: Запрашиваемый новый статус.

    Returns:
        `True`, если переход разрешён; `False` иначе. Переход статуса
        в самого себя (`current == target`) не считается допустимым —
        вызывающая сторона должна была отфильтровать это раньше, если
        такой запрос предполагается идемпотентным no-op.
    """
    return target in ORDER_STATUS_TRANSITIONS[current]