"""Фабрики сервисов для инъекции в роуты через FastAPI Depends."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.catalog import CatalogService
from app.services.category import CategoryService
from app.services.manufacturer import ManufacturerService
from app.services.product import ProductService
from app.services.promo import PromoService
from app.services.review import ReviewService
from app.services.stock import StockService

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_category_service(session: DbSession) -> CategoryService:
    """Строит `CategoryService` на сессии текущего запроса."""
    return CategoryService(session)


def get_manufacturer_service(session: DbSession) -> ManufacturerService:
    """Строит `ManufacturerService` на сессии текущего запроса."""
    return ManufacturerService(session)


def get_product_service(session: DbSession) -> ProductService:
    """Строит `ProductService` на сессии текущего запроса."""
    return ProductService(session)


def get_catalog_service(session: DbSession) -> CatalogService:
    """Строит `CatalogService` на сессии текущего запроса."""
    return CatalogService(session)


def get_review_service(session: DbSession) -> ReviewService:
    """Строит `ReviewService` на сессии текущего запроса."""
    return ReviewService(session)


def get_promo_service(session: DbSession) -> PromoService:
    """Строит `PromoService` на сессии текущего запроса."""
    return PromoService(session)


def get_stock_service(session: DbSession) -> StockService:
    """Строит `StockService` на сессии текущего запроса."""
    return StockService(session)



