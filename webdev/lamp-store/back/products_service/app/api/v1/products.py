import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_catalog_service,
    get_product_service,
    get_review_service,
)
from app.core.permissions import Permission
from app.core.security import require_permission
from app.models.enums import SocketType
from app.schemas.common import PaginatedResponse
from app.schemas.product import (
    ProductCatalogItem,
    ProductCreate,
    ProductDetail,
    ProductRead,
    ProductUpdate,
)
from app.services.catalog import CatalogService
from app.services.product import ProductService
from app.services.review import ReviewService

router = APIRouter(prefix="/products", tags=["products"])
admin_router = APIRouter(prefix="/admin/products", tags=["admin:products"])


@router.get("", response_model=PaginatedResponse[ProductCatalogItem])
async def list_products(
    service: CatalogService = Depends(get_catalog_service),
    category_id: uuid.UUID | None = Query(default=None),
    manufacturer_id: uuid.UUID | None = Query(default=None),
    socket_type: SocketType | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    in_stock_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[ProductCatalogItem]:
    """Возвращает страницу витрины с ценами, рассчитанными по акциям.

    Args:
        service: Сервис витрины.
        category_id: Фильтр по категории.
        manufacturer_id: Фильтр по производителю.
        socket_type: Фильтр по типу цоколя.
        min_price: Нижняя граница базовой цены.
        max_price: Верхняя граница базовой цены.
        search: Подстрока для поиска по названию товара.
        in_stock_only: Показывать только товары в наличии.
        limit: Размер страницы.
        offset: Смещение от начала выборки.

    Returns:
        Страницу товаров витрины с общим количеством.
    """
    items, total = await service.list_catalog(
        category_id=category_id,
        manufacturer_id=manufacturer_id,
        socket_type=socket_type,
        min_price=min_price,
        max_price=max_price,
        search=search,
        in_stock_only=in_stock_only,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(items=items, total=total)


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: uuid.UUID,
    catalog: CatalogService = Depends(get_catalog_service),
    reviews: ReviewService = Depends(get_review_service),
) -> ProductDetail:
    """Возвращает полную карточку товара для страницы товара.

    Args:
        product_id: Идентификатор товара.
        catalog: Сервис витрины.
        reviews: Сервис отзывов.

    Returns:
        Карточку товара с ценой, связями и средним рейтингом.

    """
    detail, catalog_item = await catalog.get_product_card(product_id)
    average_rating = await reviews.get_average_rating(product_id)

    return ProductDetail(
        **catalog_item.model_dump(),
        category=detail.category,
        manufacturer=detail.manufacturer,
        average_rating=average_rating,
    )


@admin_router.get("", response_model=PaginatedResponse[ProductRead])
async def admin_list_products(
    service: ProductService = Depends(get_product_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PRODUCTS)),
) -> PaginatedResponse[ProductRead]:
    """Возвращает страницу всех товаров, включая скрытые (для админки).

    Args:
        service: Сервис управления товарами.
        limit: Размер страницы.
        offset: Смещение от начала выборки.
        _claims: Проверенные claims администратора.

    Returns:
        Страницу товаров с общим количеством.
    """
    items, total = await service.list_products(
        only_active=False, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[ProductRead.model_validate(p) for p in items], total=total
    )


@admin_router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PRODUCTS)),
) -> ProductRead:
    """Создаёт товар.

    Args:
        data: Данные нового товара.
        service: Сервис управления товарами.
        _claims: Проверенные claims администратора.

    Returns:
        Созданный товар.
    """
    product = await service.create(data)
    return ProductRead.model_validate(product)


@admin_router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PRODUCTS)),
) -> ProductRead:
    """Частично обновляет товар (остаток этим методом не меняется).

    Args:
        product_id: Идентификатор товара.
        data: Изменяемые поля.
        service: Сервис управления товарами.
        _claims: Проверенные claims администратора.

    Returns:
        Обновлённый товар.
    """
    product = await service.update(product_id, data)
    return ProductRead.model_validate(product)


@admin_router.delete("/{product_id}", response_model=ProductRead)
async def deactivate_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PRODUCTS)),
) -> ProductRead:
    """Снимает товар с витрины (физическое удаление запрещено).

    Args:
        product_id: Идентификатор товара.
        service: Сервис управления товарами.
        _claims: Проверенные claims администратора.

    Returns:
        Деактивированный товар.
    """
    product = await service.deactivate(product_id)
    return ProductRead.model_validate(product)
