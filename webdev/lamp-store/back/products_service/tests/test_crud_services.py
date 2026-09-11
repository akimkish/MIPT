import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DiscountType
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.promo import PromoUpdate
from app.schemas.review import ReviewCreate
from app.services.category import CategoryService
from app.services.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.services.product import ProductService
from app.services.promo import PromoService
from app.services.review import ReviewService
from tests.factories import make_category, make_manufacturer, make_product, make_promo

pytestmark = pytest.mark.asyncio


class TestCategoryService:
    async def test_create_duplicate_name_case_insensitive_conflict(
        self, session: AsyncSession
    ) -> None:
        service = CategoryService(session)
        await service.create(CategoryCreate(name="LED"))

        with pytest.raises(ConflictError):
            await service.create(CategoryCreate(name="led"))

    async def test_deactivate_missing_category_not_found(
        self, session: AsyncSession
    ) -> None:
        service = CategoryService(session)
        with pytest.raises(NotFoundError):
            await service.deactivate(uuid.uuid4())


class TestProductService:
    async def test_create_with_missing_category_not_found(
        self, session: AsyncSession
    ) -> None:
        manufacturer = await make_manufacturer(session)
        service = ProductService(session)

        with pytest.raises(NotFoundError):
            await service.create(
                ProductCreate(
                    product_name="Lamp",
                    sku="SKU-1",
                    category_id=uuid.uuid4(),
                    manufacturer_id=manufacturer.manufacturer_id,
                    price=Decimal("10.00"),
                    quantity=1,
                    power_watts=Decimal("9.5"),
                    socket_type="E27",
                    color_temperature_k=4000,
                )
            )

    async def test_create_with_duplicate_sku_conflict(
        self, session: AsyncSession
    ) -> None:
        existing = await make_product(session, sku="SKU-DUP")
        service = ProductService(session)

        with pytest.raises(ConflictError):
            await service.create(
                ProductCreate(
                    product_name="Another lamp",
                    sku="SKU-DUP",
                    category_id=existing.category_id,
                    manufacturer_id=existing.manufacturer_id,
                    price=Decimal("10.00"),
                    quantity=1,
                    power_watts=Decimal("9.5"),
                    socket_type="E27",
                    color_temperature_k=4000,
                )
            )

    async def test_update_partial_does_not_touch_other_fields(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, price=Decimal("50.00"), quantity=7)
        service = ProductService(session)

        updated = await service.update(
            product.product_id, ProductUpdate(product_name="New name")
        )

        assert updated.product_name == "New name"
        assert updated.price == Decimal("50.00")  # не изменилось
        assert updated.quantity == 7  # quantity вообще нет в ProductUpdate

    async def test_update_category_to_missing_id_not_found(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        service = ProductService(session)

        with pytest.raises(NotFoundError):
            await service.update(
                product.product_id, ProductUpdate(category_id=uuid.uuid4())
            )


class TestReviewService:
    async def test_create_review_on_inactive_product_not_found(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session, is_active=False)
        service = ReviewService(session)

        with pytest.raises(NotFoundError):
            await service.create(
                ReviewCreate(
                    product_id=product.product_id,
                    user_name="Alice",
                    user_email="alice@example.com",
                    rating=5,
                )
            )

    async def test_create_duplicate_review_conflict_before_db_insert(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        service = ReviewService(session)
        data = ReviewCreate(
            product_id=product.product_id,
            user_name="Alice",
            user_email="alice@example.com",
            rating=5,
        )
        await service.create(data)

        with pytest.raises(ConflictError):
            await service.create(data)

    async def test_new_review_not_visible_until_approved(
        self, session: AsyncSession
    ) -> None:
        product = await make_product(session)
        service = ReviewService(session)
        review = await service.create(
            ReviewCreate(
                product_id=product.product_id,
                user_name="Bob",
                user_email="bob@example.com",
                rating=4,
            )
        )

        visible, total = await service.list_for_product(
            product.product_id, only_approved=True
        )
        assert total == 0

        await service.set_approved(review.review_id, True)
        visible, total = await service.list_for_product(
            product.product_id, only_approved=True
        )
        assert total == 1


class TestPromoService:
    async def test_update_discount_type_to_percent_with_invalid_discount_rejected(
        self, session: AsyncSession
    ) -> None:
        """discount=150 валиден для fixed, но недопустим при переключении на percent."""
        product = await make_product(session)
        promo = await make_promo(
            session,
            product=product,
            discount_type=DiscountType.FIXED.value,
            discount=Decimal("150"),
        )
        service = PromoService(session)

        with pytest.raises(DomainValidationError):
            await service.update(
                promo.promo_id, PromoUpdate(discount_type=DiscountType.PERCENT)
            )
