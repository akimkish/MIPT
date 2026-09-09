"""Фабрики тестовых данных: создают и сохраняют ORM-объекты в сессии теста."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.enums import DiscountType, SocketType
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.promo import Promo
from app.models.review import Review


async def make_category(session: AsyncSession, **overrides) -> Category:
    """Создаёт и сохраняет категорию с разумными значениями по умолчанию."""
    defaults = {"name": f"Category-{uuid.uuid4().hex[:8]}", "is_active": True}
    category = Category(**{**defaults, **overrides})
    session.add(category)
    await session.flush()
    return category


async def make_manufacturer(session: AsyncSession, **overrides) -> Manufacturer:
    """Создаёт и сохраняет производителя с разумными значениями по умолчанию."""
    defaults = {"name": f"Manufacturer-{uuid.uuid4().hex[:8]}", "is_active": True}
    manufacturer = Manufacturer(**{**defaults, **overrides})
    session.add(manufacturer)
    await session.flush()
    return manufacturer


async def make_product(session: AsyncSession, **overrides) -> Product:
    """Создаёт и сохраняет товар; при необходимости создаёт категорию/производителя."""
    category = overrides.pop("category", None) or await make_category(session)
    manufacturer = overrides.pop("manufacturer", None) or await make_manufacturer(
        session
    )
    defaults = {
        "product_name": f"Product-{uuid.uuid4().hex[:8]}",
        "sku": uuid.uuid4().hex[:12].upper(),
        "category_id": category.category_id,
        "manufacturer_id": manufacturer.manufacturer_id,
        "price": Decimal("100.00"),
        "quantity": 10,
        "power_watts": Decimal("9.5"),
        "socket_type": SocketType.E27.value,
        "color_temperature_k": 4000,
        "is_active": True,
    }
    product = Product(**{**defaults, **overrides})
    session.add(product)
    await session.flush()

    # Явно связываем relationship-атрибуты с уже загруженными объектами —
    # иначе последующее обращение к product.category/product.manufacturer
    # в тестах вызовет lazy-load, а в async-режиме это MissingGreenlet.
    product.category = category
    product.manufacturer = manufacturer
    return product


async def make_promo(session: AsyncSession, *, product: Product, **overrides) -> Promo:
    """Создаёт и сохраняет акцию на переданный товар."""
    now = datetime.now(UTC)
    defaults = {
        "promo_name": f"Promo-{uuid.uuid4().hex[:8]}",
        "discount_type": DiscountType.PERCENT.value,
        "discount": Decimal("10.00"),
        "product_id": product.product_id,
        "min_quantity": 1,
        "valid_from": now - timedelta(days=1),
        "valid_to": now + timedelta(days=1),
        "is_active": True,
    }
    promo = Promo(**{**defaults, **overrides})
    session.add(promo)
    await session.flush()
    return promo


async def make_review(session: AsyncSession, *, product: Product, **overrides) -> Review:
    """Создаёт и сохраняет отзыв на переданный товар."""
    defaults = {
        "product_id": product.product_id,
        "user_name": "Test User",
        "user_email": f"{uuid.uuid4().hex[:8]}@example.com",
        "rating": 5,
        "is_approved": False,
    }
    review = Review(**{**defaults, **overrides})
    session.add(review)
    await session.flush()
    return review