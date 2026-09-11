import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.promo import PromoRepository
from app.repositories.review import ReviewRepository
from tests.factories import make_category, make_product, make_promo, make_review

pytestmark = pytest.mark.asyncio


class TestDecreaseIncreaseQuantity:
    async def test_decrease_quantity_success(self, session: AsyncSession) -> None:
        product = await make_product(session, quantity=10)
        repo = ProductRepository(session)

        ok = await repo.decrease_quantity(product.product_id, 3)

        assert ok is True
        await session.refresh(product)
        assert product.quantity == 7

    async def test_decrease_quantity_to_exactly_zero(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, quantity=5)
        repo = ProductRepository(session)

        ok = await repo.decrease_quantity(product.product_id, 5)

        assert ok is True
        await session.refresh(product)
        assert product.quantity == 0

    async def test_decrease_quantity_one_more_than_available_fails(
        self, session: AsyncSession
    ) -> None:
        """Граница: запрос на 1 больше остатка — отказ, остаток не меняется."""
        product = await make_product(session, quantity=5)
        repo = ProductRepository(session)

        ok = await repo.decrease_quantity(product.product_id, 6)

        assert ok is False
        refreshed = await repo.get_by_id(product.product_id)
        assert refreshed.quantity == 5

    async def test_decrease_quantity_for_missing_product_returns_false(
        self, session: AsyncSession
    ) -> None:
        repo = ProductRepository(session)
        ok = await repo.decrease_quantity(uuid.uuid4(), 1)
        assert ok is False

    async def test_increase_quantity_success(self, session: AsyncSession) -> None:
        product = await make_product(session, quantity=5)
        repo = ProductRepository(session)

        ok = await repo.increase_quantity(product.product_id, 3)

        assert ok is True
        await session.refresh(product)
        assert product.quantity == 8


class TestCategoryRepository:
    async def test_get_by_name_case_insensitive(self, session: AsyncSession) -> None:
        await make_category(session, name="LED Lamps")
        repo = CategoryRepository(session)

        found = await repo.get_by_name("led lamps")

        assert found is not None
        assert found.name == "LED Lamps"

    async def test_list_all_pagination_last_partial_page(
        self, session: AsyncSession
    ) -> None:
        for _ in range(3):
            await make_category(session)
        repo = CategoryRepository(session)

        items, total = await repo.list_all(limit=2, offset=2)

        assert total == 3
        assert len(items) == 1

    async def test_list_all_offset_beyond_total_returns_empty(
        self, session: AsyncSession
    ) -> None:
        await make_category(session)
        repo = CategoryRepository(session)

        items, total = await repo.list_all(limit=20, offset=100)

        assert total == 1
        assert items == []


class TestProductRepositoryCatalogFilters:
    async def test_list_products_hides_item_when_category_inactive(
        self, session: AsyncSession
    ) -> None:
        category = await make_category(session, is_active=False)
        await make_product(session, category=category)
        repo = ProductRepository(session)

        items, total = await repo.list_products(only_active=True)

        assert total == 0
        assert items == []

    async def test_list_products_hides_item_when_manufacturer_inactive(
        self, session: AsyncSession
    ) -> None:
        manufacturer = await make_manufacturer(session, is_active=False)
        await make_product(session, manufacturer=manufacturer)
        repo = ProductRepository(session)

        items, total = await repo.list_products(only_active=True)

        assert total == 0

    async def test_get_many_by_ids_partial_missing(self, session: AsyncSession) -> None:
        product = await make_product(session)
        repo = ProductRepository(session)

        found = await repo.get_many_by_ids([product.product_id, uuid.uuid4()])

        assert len(found) == 1
        assert found[0].product_id == product.product_id


class TestPromoRepositoryDateWindow:
    async def test_promo_active_at_valid_from_boundary(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        now = datetime.now(UTC)
        await make_promo(
            session, product=product, valid_from=now, valid_to=now + timedelta(days=1)
        )
        repo = PromoRepository(session)

        found = await repo.list_active_for_product(product.product_id, at=now)

        assert len(found) == 1

    async def test_promo_not_active_before_valid_from(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        now = datetime.now(UTC)
        await make_promo(
            session,
            product=product,
            valid_from=now + timedelta(seconds=1),
            valid_to=now + timedelta(days=1),
        )
        repo = PromoRepository(session)

        found = await repo.list_active_for_product(product.product_id, at=now)

        assert found == []


class TestReviewRepository:
    async def test_delete_nonexistent_review_returns_false(
        self, session: AsyncSession
    ) -> None:
        repo = ReviewRepository(session)
        deleted = await repo.delete_by_id(uuid.uuid4())
        assert deleted is False


from tests.factories import (
    make_manufacturer,
)
