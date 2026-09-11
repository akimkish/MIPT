import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StockOperationType
from app.models.product import Product
from app.models.review import Review
from app.models.stock_operation import StockOperation
from tests.factories import make_category, make_manufacturer, make_product, make_review

pytestmark = pytest.mark.asyncio


class TestProductChecks:
    """CHECK-ограничения таблицы products."""

    @pytest.mark.parametrize("power_watts", [Decimal("0.1"), Decimal("100")])
    async def test_power_watts_positive_boundary_ok(
        self, session: AsyncSession, power_watts: Decimal
    ) -> None:
        product = await make_product(session, power_watts=power_watts)
        await session.flush()
        assert product.product_id is not None

    async def test_power_watts_zero_rejected(self, session: AsyncSession) -> None:
        with pytest.raises(IntegrityError):
            await make_product(session, power_watts=Decimal("0"))

    @pytest.mark.parametrize("temperature", [1000, 10000])
    async def test_color_temperature_boundary_ok(
        self, session: AsyncSession, temperature: int
    ) -> None:
        product = await make_product(session, color_temperature_k=temperature)
        assert product.color_temperature_k == temperature

    @pytest.mark.parametrize("temperature", [999, 10001])
    async def test_color_temperature_out_of_range_rejected(
        self, session: AsyncSession, temperature: int
    ) -> None:
        with pytest.raises(IntegrityError):
            await make_product(session, color_temperature_k=temperature)

    async def test_socket_type_outside_allowed_list_rejected(
        self, session: AsyncSession
    ) -> None:
        """known_limitations: INSERT со значением вне списка отбивается CHECK."""
        with pytest.raises(IntegrityError):
            await make_product(session, socket_type="WAT")

    async def test_sku_uniqueness(self, session: AsyncSession) -> None:
        await make_product(session, sku="DUPLICATE-1")
        with pytest.raises(IntegrityError):
            await make_product(session, sku="DUPLICATE-1")


class TestReviewChecks:
    """CHECK/UNIQUE-ограничения таблицы reviews."""

    @pytest.mark.parametrize("rating", [1, 5])
    async def test_rating_boundary_ok(self, session: AsyncSession, rating: int) -> None:
        product = await make_product(session)
        review = await make_review(session, product=product, rating=rating)
        assert review.rating == rating

    @pytest.mark.parametrize("rating", [0, 6])
    async def test_rating_out_of_range_rejected(
        self, session: AsyncSession, rating: int
    ) -> None:
        product = await make_product(session)
        with pytest.raises(IntegrityError):
            await make_review(session, product=product, rating=rating)

    async def test_duplicate_review_same_email_rejected(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        await make_review(session, product=product, user_email="a@example.com")
        with pytest.raises(IntegrityError):
            await make_review(session, product=product, user_email="a@example.com")


class TestPromoChecks:
    """CHECK-ограничения таблицы promos."""

    async def test_percent_discount_boundary_100_ok(
        self, session: AsyncSession
    ) -> None:
        from tests.factories import make_promo

        product = await make_product(session)
        promo = await make_promo(session, product=product, discount=Decimal("100"))
        assert promo.discount == Decimal("100")

    async def test_percent_discount_over_100_rejected(
        self, session: AsyncSession
    ) -> None:
        from tests.factories import make_promo

        product = await make_product(session)
        with pytest.raises(IntegrityError):
            await make_promo(session, product=product, discount=Decimal("100.01"))

    async def test_min_quantity_zero_rejected(self, session: AsyncSession) -> None:
        from tests.factories import make_promo

        product = await make_product(session)
        with pytest.raises(IntegrityError):
            await make_promo(session, product=product, min_quantity=0)

    async def test_valid_from_equal_valid_to_rejected(
        self, session: AsyncSession
    ) -> None:
        from tests.factories import make_promo

        product = await make_product(session)
        now = datetime.now(UTC)
        with pytest.raises(IntegrityError):
            await make_promo(session, product=product, valid_from=now, valid_to=now)


class TestUniqueCaseInsensitiveNames:
    """Функциональный индекс по lower(name) для категорий и производителей."""

    async def test_category_name_unique_case_insensitive(
        self, session: AsyncSession
    ) -> None:
        await make_category(session, name="LED")
        with pytest.raises(IntegrityError):
            await make_category(session, name="led")

    async def test_manufacturer_name_unique_case_insensitive(
        self, session: AsyncSession
    ) -> None:
        await make_manufacturer(session, name="Philips")
        with pytest.raises(IntegrityError):
            await make_manufacturer(session, name="philips")


class TestOnDeleteRestrict:
    """Запрет удаления справочников, на которые ссылаются товары."""

    async def test_cannot_delete_category_referenced_by_product(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        await session.delete(product.category)
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_cannot_delete_manufacturer_referenced_by_product(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        await session.delete(product.manufacturer)
        with pytest.raises(IntegrityError):
            await session.flush()


class TestStockOperationCompositeKey:
    """Составной первичный ключ (order_id, operation) — основа идемпотентности."""

    async def test_duplicate_operation_for_same_order_rejected(
        self, session: AsyncSession
    ) -> None:
        order_id = uuid.uuid4()
        session.add(
            StockOperation(
                order_id=order_id, operation=StockOperationType.RESERVE.value
            )
        )
        await session.flush()
        session.add(
            StockOperation(
                order_id=order_id, operation=StockOperationType.RESERVE.value
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_reserve_and_release_for_same_order_allowed(
        self, session: AsyncSession
    ) -> None:
        """Разные operation — разные строки, PK не конфликтует."""
        order_id = uuid.uuid4()
        session.add(
            StockOperation(
                order_id=order_id, operation=StockOperationType.RESERVE.value
            )
        )
        session.add(
            StockOperation(
                order_id=order_id, operation=StockOperationType.RELEASE.value
            )
        )
        await session.flush()
