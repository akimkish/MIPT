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
    return CategoryService(session)


def get_manufacturer_service(session: DbSession) -> ManufacturerService:
    return ManufacturerService(session)


def get_product_service(session: DbSession) -> ProductService:
    return ProductService(session)


def get_catalog_service(session: DbSession) -> CatalogService:
    return CatalogService(session)


def get_review_service(session: DbSession) -> ReviewService:
    return ReviewService(session)


def get_promo_service(session: DbSession) -> PromoService:
    return PromoService(session)


def get_stock_service(session: DbSession) -> StockService:
    return StockService(session)
