import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import OrderStatus
from app.repositories.order_repository import OrderRepository
from tests.conftest import make_order, make_order_item


@pytest.mark.asyncio
async def test_get_by_id_loads_items(db_session: AsyncSession) -> None:
    """11. get_by_id возвращает заказ с уже загруженными items."""
    order = make_order()
    db_session.add(order)
    await db_session.flush()
    db_session.add(make_order_item(order))
    await db_session.flush()

    repo = OrderRepository(db_session)
    found = await repo.get_by_id(order.order_id)

    assert found is not None
    assert len(found.items) == 1


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_missing(db_session: AsyncSession) -> None:
    """12. get_by_id возвращает None для несуществующего заказа."""
    repo = OrderRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_get_by_idempotency_key(db_session: AsyncSession) -> None:
    """13. Поиск по ключу идемпотентности: найден / не найден."""
    key = f"idem-{uuid.uuid4()}"
    order = make_order(idempotency_key=key)
    db_session.add(order)
    await db_session.flush()

    repo = OrderRepository(db_session)
    assert (await repo.get_by_idempotency_key(key)).order_id == order.order_id
    assert await repo.get_by_idempotency_key("no-such-key") is None


@pytest.mark.asyncio
async def test_list_orders_without_filters(db_session: AsyncSession) -> None:
    """14. Список без фильтров возвращает все заказы, total совпадает."""
    for _ in range(3):
        db_session.add(make_order())
    await db_session.flush()

    repo = OrderRepository(db_session)
    items, total = await repo.list_orders()

    assert total == 3
    assert len(items) == 3


@pytest.mark.asyncio
async def test_list_orders_filters_by_status(db_session: AsyncSession) -> None:
    """15. Фильтр по статусу отбирает только нужные заказы."""
    db_session.add(make_order(status=OrderStatus.PAID.value))
    db_session.add(make_order(status=OrderStatus.NEW.value))
    await db_session.flush()

    repo = OrderRepository(db_session)
    items, total = await repo.list_orders(status=OrderStatus.PAID)

    assert total == 1
    assert items[0].status == OrderStatus.PAID.value


@pytest.mark.asyncio
async def test_list_orders_filters_by_exact_email(db_session: AsyncSession) -> None:
    """16. Фильтр по email — точное совпадение, без нормализации регистра."""
    db_session.add(make_order(email="buyer@example.com"))
    await db_session.flush()

    repo = OrderRepository(db_session)
    _, exact_total = await repo.list_orders(email="buyer@example.com")
    _, mismatched_total = await repo.list_orders(email="BUYER@EXAMPLE.COM")

    assert exact_total == 1
    assert mismatched_total == 0


@pytest.mark.asyncio
async def test_list_orders_combines_status_and_email(db_session: AsyncSession) -> None:
    """17. Фильтры status и email применяются одновременно (AND)."""
    db_session.add(make_order(email="a@example.com", status=OrderStatus.PAID.value))
    db_session.add(make_order(email="a@example.com", status=OrderStatus.NEW.value))
    db_session.add(make_order(email="b@example.com", status=OrderStatus.PAID.value))
    await db_session.flush()

    repo = OrderRepository(db_session)
    _, total = await repo.list_orders(status=OrderStatus.PAID, email="a@example.com")

    assert total == 1


@pytest.mark.asyncio
async def test_list_orders_pagination(db_session: AsyncSession) -> None:
    """18. limit/offset возвращают корректную подстраницу, total не зависит от них."""
    for _ in range(5):
        db_session.add(make_order())
    await db_session.flush()

    repo = OrderRepository(db_session)
    page, total = await repo.list_orders(limit=2, offset=2)

    assert total == 5
    assert len(page) == 2


@pytest.mark.asyncio
async def test_list_orders_offset_beyond_total(db_session: AsyncSession) -> None:
    """19. Edge-case: offset больше общего количества — пустая страница, total верен."""
    db_session.add(make_order())
    await db_session.flush()

    repo = OrderRepository(db_session)
    page, total = await repo.list_orders(limit=20, offset=1000)

    assert page == []
    assert total == 1


@pytest.mark.asyncio
async def test_update_status_changes_status(db_session: AsyncSession) -> None:
    """20. update_status меняет статус существующего заказа."""
    order = make_order(status=OrderStatus.NEW.value)
    db_session.add(order)
    await db_session.flush()

    repo = OrderRepository(db_session)
    updated = await repo.update_status(order, OrderStatus.PAID)

    assert updated.status == OrderStatus.PAID.value


@pytest.mark.asyncio
async def test_concurrent_status_update_last_write_wins(
    db_session: AsyncSession,
) -> None:
    order = make_order(status=OrderStatus.NEW.value)
    db_session.add(order)
    await db_session.flush()
    order_id = order.order_id

    connection = await db_session.connection()
    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async with session_factory() as session_a:
        order_a = await OrderRepository(session_a).get_by_id(order_id)
        await OrderRepository(session_a).update_status(order_a, OrderStatus.PAID)
        await session_a.commit()

    async with session_factory() as session_b:
        order_b = await OrderRepository(session_b).get_by_id(order_id)
        await OrderRepository(session_b).update_status(order_b, OrderStatus.CANCELLED)
        await session_b.commit()

    db_session.expire(order)
    final = await OrderRepository(db_session).get_by_id(order_id)
    assert final.status == OrderStatus.CANCELLED.value
