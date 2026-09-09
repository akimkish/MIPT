"""Тесты ценообразования и витрины. Предполагает применённый фикс из проблемы 3."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DiscountType
from app.services.catalog import (
    CatalogService,
    apply_promo,
    calculate_total_price,
    calculate_unit_price,
    round_money,
)
from app.services.exceptions import NotFoundError
from tests.factories import make_category, make_manufacturer, make_product, make_promo

pytestmark = pytest.mark.asyncio


class TestRoundMoney:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Decimal("2.345"), Decimal("2.35")),  # ROUND_HALF_UP, не банковское
            (Decimal("2.344"), Decimal("2.34")),
            (Decimal("100.00"), Decimal("100.00")),
        ],
    )
    def test_rounding_half_up(self, value: Decimal, expected: Decimal) -> None:
        assert round_money(value) == expected


class TestApplyPromo:
    def test_percent_discount(self) -> None:
        from app.models.promo import Promo

        promo = Promo(discount_type=DiscountType.PERCENT.value, discount=Decimal("10"))
        assert apply_promo(Decimal("100.00"), promo) == Decimal("90.00")

    def test_fixed_discount_larger_than_price_clamped_to_zero(self) -> None:
        """Доменный тест из ТЗ: фикс. скидка больше цены не даёт отрицательную цену."""
        from app.models.promo import Promo

        promo = Promo(discount_type=DiscountType.FIXED.value, discount=Decimal("500"))
        assert apply_promo(Decimal("80.00"), promo) == Decimal("0.00")

    def test_fixed_discount_equal_to_price_gives_zero(self) -> None:
        from app.models.promo import Promo

        promo = Promo(discount_type=DiscountType.FIXED.value, discount=Decimal("80"))
        assert apply_promo(Decimal("80.00"), promo) == Decimal("0.00")


class TestCalculateUnitPrice:
    def test_no_promos_returns_base_price(self) -> None:
        quote = calculate_unit_price(Decimal("100.00"), [], quantity=1)
        assert quote.unit_price == Decimal("100.00")
        assert quote.promo_id is None

    def test_selects_promo_with_maximum_discount(self) -> None:
        """Доменный тест из ТЗ: выбор акции с максимальной скидкой, без суммирования."""
        from app.models.promo import Promo
        import uuid

        cheap_promo_id = uuid.uuid4()
        promos = [
            Promo(
                promo_id=uuid.uuid4(),
                discount_type=DiscountType.PERCENT.value,
                discount=Decimal("10"),
                min_quantity=1,
            ),
            Promo(
                promo_id=cheap_promo_id,
                discount_type=DiscountType.PERCENT.value,
                discount=Decimal("25"),
                min_quantity=1,
            ),
        ]

        quote = calculate_unit_price(Decimal("100.00"), promos, quantity=1)

        assert quote.unit_price == Decimal("75.00")
        assert quote.promo_id == cheap_promo_id

    def test_min_quantity_boundary_applies_exactly_at_threshold(self) -> None:
        from app.models.promo import Promo

        promo = Promo(
            discount_type=DiscountType.PERCENT.value, discount=Decimal("10"), min_quantity=3
        )
        quote_at_threshold = calculate_unit_price(Decimal("100.00"), [promo], quantity=3)
        quote_below_threshold = calculate_unit_price(Decimal("100.00"), [promo], quantity=2)

        assert quote_at_threshold.unit_price == Decimal("90.00")
        assert quote_below_threshold.unit_price == Decimal("100.00")


class TestCalculateTotalPrice:
    def test_total_equals_rounded_unit_times_quantity(self) -> None:
        """Округление unit_price происходит до умножения, не после."""
        unit_price = round_money(Decimal("33.333"))  # -> 33.33
        total = calculate_total_price(unit_price, quantity=3)
        assert total == Decimal("99.99")


class TestCatalogServiceCard:
    async def test_get_product_card_hidden_when_category_inactive(
        self, session: AsyncSession
    ) -> None:
        category = await make_category(session, is_active=False)
        product = await make_product(session, category=category)
        service = CatalogService(session)

        with pytest.raises(NotFoundError):
            await service.get_product_card(product.product_id)

    async def test_get_product_card_returns_display_price_with_active_promo(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, price=Decimal("200.00"))
        await make_promo(session, product=product, discount=Decimal("50"), discount_type=DiscountType.FIXED.value)
        service = CatalogService(session)

        _, catalog_item = await service.get_product_card(product.product_id)

        assert catalog_item.display_price == Decimal("150.00")

    async def test_bulk_discount_hint_uses_lowest_min_quantity(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        await make_promo(session, product=product, min_quantity=5)
        await make_promo(session, product=product, min_quantity=3)
        service = CatalogService(session)

        _, catalog_item = await service.get_product_card(product.product_id)

        assert catalog_item.bulk_discount_hint == "от 3 шт. дешевле"


class TestCatalogServiceQuoteItems:
    async def test_quote_items_raises_for_any_missing_product(
        self, session: AsyncSession
    ) -> None:
        import uuid

        product = await make_product(session)
        service = CatalogService(session)
        missing_id = uuid.uuid4()

        with pytest.raises(NotFoundError):
            await service.quote_items({product.product_id: 1, missing_id: 1})