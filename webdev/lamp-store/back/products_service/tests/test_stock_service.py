import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.repositories.product import ProductRepository
from app.schemas.stock import StockItem
from app.services.exceptions import (
    ConflictError,
    DomainValidationError,
    InsufficientStockError,
)
from app.services.stock import StockService
from tests.factories import make_product

pytestmark = pytest.mark.asyncio


class TestReserveHappyPath:
    async def test_reserve_multiple_items_decreases_stock_atomically(
        self, session: AsyncSession
    ) -> None:
        product_a = await make_product(session, quantity=10)
        product_b = await make_product(session, quantity=10)
        service = StockService(session)
        order_id = uuid.uuid4()

        result = await service.reserve(
            order_id,
            [
                StockItem(product_id=product_a.product_id, quantity=3),
                StockItem(product_id=product_b.product_id, quantity=5),
            ],
        )

        assert result.already_applied is False
        await session.refresh(product_a)
        await session.refresh(product_b)
        assert product_a.quantity == 7
        assert product_b.quantity == 5

    async def test_release_returns_stock_from_reserve_snapshot(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, quantity=10)
        service = StockService(session)
        order_id = uuid.uuid4()

        await service.reserve(
            order_id, [StockItem(product_id=product.product_id, quantity=4)]
        )
        result = await service.release(order_id)

        assert result.already_applied is False
        repo = ProductRepository(session)
        assert (await repo.get_by_id(product.product_id)).quantity == 10


class TestReserveValidation:
    async def test_reserve_empty_items_rejected(self, session: AsyncSession) -> None:
        service = StockService(session)
        with pytest.raises(DomainValidationError):
            await service.reserve(uuid.uuid4(), [])

    async def test_reserve_duplicate_product_in_items_rejected(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, quantity=10)
        service = StockService(session)
        with pytest.raises(DomainValidationError):
            await service.reserve(
                uuid.uuid4(),
                [
                    StockItem(product_id=product.product_id, quantity=1),
                    StockItem(product_id=product.product_id, quantity=2),
                ],
            )


class TestReserveIdempotency:
    async def test_repeated_reserve_same_order_is_noop(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, quantity=10)
        service = StockService(session)
        order_id = uuid.uuid4()

        first = await service.reserve(
            order_id, [StockItem(product_id=product.product_id, quantity=3)]
        )
        second = await service.reserve(
            order_id, [StockItem(product_id=product.product_id, quantity=3)]
        )

        assert first.already_applied is False
        assert second.already_applied is True
        await session.refresh(product)
        assert product.quantity == 7  # не списано дважды


class TestReservePartialFailureAtomicity:
    async def test_partial_stock_shortage_rolls_back_entire_reserve(
        self, session: AsyncSession
    ) -> None:
        """Первая позиция могла бы списаться, вторая — нет: обе должны откатиться."""
        enough = await make_product(session, quantity=10)
        not_enough = await make_product(session, quantity=1)
        # Явный commit фиксирует arrange-состояние отдельным savepoint-чекпоинтом.
        # Без него rollback() внутри reserve() (join_transaction_mode="create_savepoint")
        # откатывает и создание этих тестовых товаров, а не только неудавшийся reserve.
        await session.commit()

        service = StockService(session)

        with pytest.raises(InsufficientStockError):
            await service.reserve(
                uuid.uuid4(),
                [
                    StockItem(product_id=enough.product_id, quantity=5),
                    StockItem(product_id=not_enough.product_id, quantity=5),
                ],
            )

        await session.refresh(enough)
        await session.refresh(not_enough)
        assert enough.quantity == 10
        assert not_enough.quantity == 1


class TestReleaseWithoutReserve:
    async def test_release_without_prior_reserve_raises_conflict(
        self, session: AsyncSession
    ) -> None:
        service = StockService(session)
        with pytest.raises(ConflictError):
            await service.release(uuid.uuid4())

    async def test_repeated_release_is_noop(self, session: AsyncSession) -> None:
        product = await make_product(session, quantity=10)
        service = StockService(session)
        order_id = uuid.uuid4()

        await service.reserve(
            order_id, [StockItem(product_id=product.product_id, quantity=4)]
        )
        await service.release(order_id)
        second_release = await service.release(order_id)

        assert second_release.already_applied is True
        repo = ProductRepository(session)
        # Повторный release не должен увеличить остаток ещё раз.
        assert (await repo.get_by_id(product.product_id)).quantity == 10


@pytest.mark.usefixtures("engine")
class TestReserveConcurrency:
    """Тесты реальной гонки требуют двух независимых транзакций/соединений.

    Стандартная фикстура `session` из conftest.py оборачивает тест в одну
    внешнюю транзакцию (SAVEPOINT-паттерн) — внутри неё нельзя получить два
    по-настоящему параллельных, независимо коммитящихся соединения. Поэтому
    здесь сессии создаются напрямую от `engine`, а созданные данные удаляются
    вручную в конце теста.
    """

    async def test_two_concurrent_orders_for_last_unit_only_one_succeeds(
        self, engine: AsyncEngine
    ) -> None:
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)

        async with factory() as setup_session:
            product = await make_product(setup_session, quantity=1)
            await setup_session.commit()
            product_id = product.product_id

        order_a, order_b = uuid.uuid4(), uuid.uuid4()

        async def _reserve(order_id: uuid.UUID) -> Exception | None:
            async with factory() as s:
                service = StockService(s)
                try:
                    await service.reserve(
                        order_id, [StockItem(product_id=product_id, quantity=1)]
                    )
                    return None
                except InsufficientStockError as exc:
                    return exc

        results = await asyncio.gather(_reserve(order_a), _reserve(order_b))

        successes = [r for r in results if r is None]
        failures = [r for r in results if r is not None]
        assert len(successes) == 1
        assert len(failures) == 1
        assert isinstance(failures[0], InsufficientStockError)

        async with factory() as check_session:
            repo = ProductRepository(check_session)
            final_product = await repo.get_by_id(product_id)
            assert final_product.quantity == 0  # не ушёл в минус

            # Уборка за собой: фикстура `session` тут не участвовала,
            # откат транзакции автоматически не произойдёт.
            await check_session.delete(final_product)
            await check_session.commit()

    async def test_concurrent_reserve_same_new_order_id_only_one_writes_journal(
        self, engine: AsyncEngine
    ) -> None:
        """Два параллельных ретрая одного order_id: не должно быть двойного списания."""
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)

        async with factory() as setup_session:
            product = await make_product(setup_session, quantity=10)
            await setup_session.commit()
            product_id = product.product_id

        order_id = uuid.uuid4()

        async def _reserve() -> None:
            async with factory() as s:
                service = StockService(s)
                await service.reserve(
                    order_id, [StockItem(product_id=product_id, quantity=3)]
                )

        await asyncio.gather(_reserve(), _reserve())

        async with factory() as check_session:
            repo = ProductRepository(check_session)
            final_product = await repo.get_by_id(product_id)
            # Списано ровно один раз, а не дважды (10 - 3 = 7, не 4).
            assert final_product.quantity == 7

            await check_session.delete(final_product)
            await check_session.execute(
                __import__("sqlalchemy").delete(
                    __import__(
                        "app.models.stock_operation", fromlist=["StockOperation"]
                    ).StockOperation
                )
            )
            await check_session.commit()
