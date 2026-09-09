# orders_service/app/api/v1/orders.py
"""Эндпоинты заказов: административные и публичное оформление.

Роутер намеренно смешанный. Общей зависимости аутентификации на нём НЕТ:
`POST /orders` публичный (учётных записей у покупателей нет), а права
проверяются на каждом административном эндпоинте отдельно. Если однажды
понадобится закрыть весь роутер целиком, оформление придётся вынести
в отдельный роутер — сейчас это лишняя сущность.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_order_service
from app.clients.products import ProductsClient
from app.core.permissions import Permission
from app.core.security import CurrentAdmin, require_permission
from app.db.database import get_session
from app.models.enums import OrderStatus
from app.repositories.order_repository import OrderRepository
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate
from app.services.checkout import CheckoutService
from app.services.exceptions import (
    CatalogItemUnavailableError,
    CheckoutUnavailableError,
    DuplicateOrderError,
    OutOfStockError,
)
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

RETRY_AFTER_SECONDS = "5"


def get_products_client(request: Request) -> ProductsClient:
    """Достаёт единственный клиент products_service из состояния приложения.

    Клиент создаётся в lifespan, а не на запрос: httpx.AsyncClient держит
    пул соединений, пересоздавать его каждый раз дорого.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        Клиент products_service.
    """
    return request.app.state.products_client


def get_checkout_service(
    session: AsyncSession = Depends(get_session),
    products: ProductsClient = Depends(get_products_client),
) -> CheckoutService:
    """Собирает сервис оформления заказа.

    Args:
        session: Сессия БД orders_service.
        products: Клиент products_service.

    Returns:
        Готовый CheckoutService.
    """
    return CheckoutService(OrderRepository(session), products)


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Оформить заказ",
)
async def create_order(
    payload: OrderCreate,
    service: CheckoutService = Depends(get_checkout_service),
) -> OrderRead:
    """Оформляет заказ покупателя.

    Эндпоинт публичный: учётных записей у покупателей нет, аутентификация
    не требуется.

    Args:
        payload: Данные покупателя, позиции корзины и idempotency_key.
        service: Сервис оформления заказа.

    Returns:
        Созданный заказ со снимком позиций.

    Raises:
        HTTPException: 409 при дубле, нехватке остатка или снятом с продажи
            товаре; 503 при недоступности products_service.
    """
    try:
        order = await service.create_order(payload)
    except (DuplicateOrderError, OutOfStockError, CatalogItemUnavailableError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        ) from exc
    except CheckoutUnavailableError as exc:
        # Тип исходного исключения на ответ покупателю не влияет: он влиял
        # только на решение о компенсации внутри саги.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": exc.code, "message": exc.message, "details": None},
            headers={"Retry-After": RETRY_AFTER_SECONDS},
        ) from exc

    return OrderRead.model_validate(order)


@router.get("", response_model=PaginatedResponse[OrderRead])
async def list_orders(
    service: OrderService = Depends(get_order_service),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    email: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: CurrentAdmin = Depends(require_permission(Permission.MANAGE_ORDERS)),
) -> PaginatedResponse[OrderRead]:
    """Возвращает страницу заказов с фильтрами по статусу и email.

    Args:
        service: Сервис заказов.
        status_filter: Фильтр по статусу (параметр запроса `status`).
        email: Фильтр по email покупателя.
        limit: Размер страницы.
        offset: Смещение от начала выборки.
        _admin: Админ из токена; нужен только ради проверки прав.

    Returns:
        Страницу заказов и их общее количество.
    """
    items, total = await service.list_orders(
        status=status_filter, email=email, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[OrderRead.model_validate(o) for o in items], total=total
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    service: OrderService = Depends(get_order_service),
    _admin: CurrentAdmin = Depends(require_permission(Permission.MANAGE_ORDERS)),
) -> OrderRead:
    """Возвращает заказ с позициями по идентификатору.

    Args:
        order_id: Идентификатор заказа.
        service: Сервис заказов.
        _admin: Админ из токена; нужен только ради проверки прав.

    Returns:
        Заказ со списком позиций.
    """
    order = await service.get(order_id)
    return OrderRead.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    service: OrderService = Depends(get_order_service),
    _admin: CurrentAdmin = Depends(require_permission(Permission.MANAGE_ORDERS)),
) -> OrderRead:
    """Переводит заказ в новый статус по правилам допустимых переходов.

    Платёжной системы в проекте нет, поэтому статусы paid/shipped/completed
    проставляет админ вручную через этот эндпоинт.

    Args:
        order_id: Идентификатор заказа.
        data: Новый статус.
        service: Сервис заказов.
        _admin: Админ из токена; нужен только ради проверки прав.

    Returns:
        Заказ с обновлённым статусом.
    """
    order = await service.update_status(order_id, data.status)
    return OrderRead.model_validate(order)