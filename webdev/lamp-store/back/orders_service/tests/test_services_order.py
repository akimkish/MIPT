import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.order_status import ORDER_STATUS_TRANSITIONS, is_transition_allowed
from app.models.enums import OrderStatus
from app.services.exceptions import ConflictError, NotFoundError
from app.services.order import OrderService
from tests.conftest import make_order


@pytest.mark.asyncio
async def test_get_existing_order(db_session: AsyncSession) -> None:
    """23. get возвращает существующий заказ."""
    order = make_order()
    db_session.add(order)
    await db_session.flush()

    service = OrderService(db_session)
    found = await service.get(order.order_id)

    assert found.order_id == order.order_id


@pytest.mark.asyncio
async def test_get_missing_order_raises_not_found(db_session: AsyncSession) -> None:
    """24. get выбрасывает NotFoundError для несуществующего заказа."""
    service = OrderService(db_session)
    with pytest.raises(NotFoundError):
        await service.get(uuid.uuid4())


@pytest.mark.asyncio
async def test_list_orders_normalizes_email_case(
    db_session: AsyncSession, mocker
) -> None:
    """25. list_orders приводит email к нижнему регистру перед вызовом репозитория."""
    service = OrderService(db_session)
    spy = mocker.patch.object(
        service._repository, "list_orders", return_value=([], 0)
    )

    await service.list_orders(email="BUYER@EXAMPLE.COM")

    spy.assert_awaited_once()
    assert spy.await_args.kwargs["email"] == "buyer@example.com"


@pytest.mark.asyncio
async def test_list_orders_without_email_passes_none(
    db_session: AsyncSession, mocker
) -> None:
    """26. list_orders(email=None) не падает и не подменяет None пустой строкой."""
    service = OrderService(db_session)
    spy = mocker.patch.object(
        service._repository, "list_orders", return_value=([], 0)
    )

    await service.list_orders(email=None)

    assert spy.await_args.kwargs["email"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("current", "target"),
    [
        (OrderStatus.NEW, OrderStatus.PAID),  # 27
        (OrderStatus.PAID, OrderStatus.SHIPPED),  # 28
        (OrderStatus.SHIPPED, OrderStatus.COMPLETED),  # 29
        (OrderStatus.NEW, OrderStatus.CANCELLED),  # 30a
        (OrderStatus.PAID, OrderStatus.CANCELLED),  # 30b
    ],
)
async def test_allowed_status_transitions_happy_path(
    db_session: AsyncSession, current: OrderStatus, target: OrderStatus
) -> None:
    """27-30. Разрешённые переходы статуса выполняются успешно."""
    order = make_order(status=current.value)
    db_session.add(order)
    await db_session.flush()

    service = OrderService(db_session)
    updated = await service.update_status(order.order_id, target)

    assert updated.status == target.value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("current", "target"),
    [
        (OrderStatus.SHIPPED, OrderStatus.NEW),  # 31: откат назад
        (OrderStatus.COMPLETED, OrderStatus.NEW),  # 32a: из терминального
        (OrderStatus.COMPLETED, OrderStatus.CANCELLED),  # 32b
        (OrderStatus.CANCELLED, OrderStatus.NEW),  # 32c
        (OrderStatus.PAID, OrderStatus.PAID),  # 33: переход в тот же статус
    ],
)
async def test_disallowed_status_transitions_raise_conflict(
    db_session: AsyncSession, current: OrderStatus, target: OrderStatus
) -> None:
    """31-33. Недопустимые переходы (включая откат и self-transition) дают ConflictError.
    """
    order = make_order(status=current.value)
    db_session.add(order)
    await db_session.flush()

    service = OrderService(db_session)
    with pytest.raises(ConflictError):
        await service.update_status(order.order_id, target)

    await db_session.refresh(order)
    assert order.status == current.value


@pytest.mark.asyncio
async def test_update_status_missing_order_raises_not_found(
    db_session: AsyncSession,
) -> None:
    """34. update_status для несуществующего заказа — NotFoundError, а не ConflictError."""
    service = OrderService(db_session)
    with pytest.raises(NotFoundError):
        await service.update_status(uuid.uuid4(), OrderStatus.PAID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "current",
    [
        OrderStatus.NEW,
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    ],
)
@pytest.mark.parametrize("target", [OrderStatus.PENDING, OrderStatus.FAILED])
async def test_cannot_manually_set_service_statuses(
    db_session: AsyncSession, current: OrderStatus, target: OrderStatus
) -> None:
    """35. Edge-case: pending/failed недостижимы через ручную смену статуса."""
    order = make_order(status=current.value)
    db_session.add(order)
    await db_session.flush()

    service = OrderService(db_session)
    with pytest.raises(ConflictError):
        await service.update_status(order.order_id, target)


def test_all_statuses_present_in_transition_graph() -> None:
    """36. Каждое значение OrderStatus — ключ в ORDER_STATUS_TRANSITIONS.
    """
    assert set(ORDER_STATUS_TRANSITIONS.keys()) == set(OrderStatus)


@pytest.mark.parametrize("status", list(OrderStatus))
def test_is_transition_allowed_never_raises_for_known_status(
    status: OrderStatus,
) -> None:
    """Вспомогательная проверка: is_transition_allowed не падает ни для одного статуса."""
    for target in OrderStatus:
        is_transition_allowed(status, target)  # не должно бросить KeyError