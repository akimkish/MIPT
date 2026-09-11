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


def is_transition_allowed(current: OrderStatus, target: OrderStatus) -> bool:

    return target in ORDER_STATUS_TRANSITIONS[current]
