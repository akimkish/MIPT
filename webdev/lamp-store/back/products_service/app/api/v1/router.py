"""Сборка всех роутеров v1 в один объект для подключения в `main.py`."""

from fastapi import APIRouter

from app.api.v1 import categories, internal, manufacturers, products, promos, reviews

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(categories.router)
api_router.include_router(categories.admin_router)
api_router.include_router(manufacturers.router)
api_router.include_router(manufacturers.admin_router)
api_router.include_router(products.router)
api_router.include_router(products.admin_router)
api_router.include_router(reviews.router)
api_router.include_router(reviews.admin_router)
api_router.include_router(promos.admin_router)
api_router.include_router(internal.router)