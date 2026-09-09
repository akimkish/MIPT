# products_service/app/api/v1/internal.py
"""Service-to-service эндпоинты: остатки и расчёт цен корзины.

Аутентификация — service-token (`verify_service_token`), а не
пользовательский JWT: вызывающая сторона — orders_service, а не браузер.
Зависимость висит на роутере, поэтому забыть её на новом эндпоинте
невозможно.

`include_in_schema=False`: внутренние эндпоинты не должны появляться
в публичном /openapi.json — иначе покупатель увидит в документации
способ дёргать склад напрямую.

Схемы запроса/ответа расчёта цен вынесены в `app/schemas/pricing.py`,
чтобы слой api оставался тонким.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_catalog_service, get_stock_service
from app.core.security import verify_service_token
from app.schemas.pricing import CartQuoteListOut, CartQuoteOut, CartQuoteRequest
from app.schemas.stock import (
    StockOperationResult,
    StockReleaseRequest,
    StockReserveRequest,
)
from app.services.catalog import CatalogService
from app.services.stock import StockService

router = APIRouter(
    prefix="/internal/stock",
    tags=["internal:stock"],
    dependencies=[Depends(verify_service_token)],
    include_in_schema=False,
)


@router.post(
    "/reserve",
    response_model=StockOperationResult,
    status_code=status.HTTP_200_OK,
)
async def reserve_stock(
    data: StockReserveRequest,
    service: StockService = Depends(get_stock_service),
) -> StockOperationResult:
    """Атомарно списывает остаток по всем позициям заказа.

    Идемпотентен по `order_id`: повторный вызов с тем же `order_id`
    не спишет остаток второй раз.

    Цены здесь НЕ считаются: снимок для заказа orders_service берёт
    отдельным вызовом `/prices` до резерва.

    Args:
        data: Идентификатор заказа и список позиций.
        service: Сервис складских операций.

    Returns:
        Результат операции с флагом `already_applied`.

    Raises:
        DomainValidationError: Если список позиций пуст или содержит
            повторяющийся товар (транслируется в HTTP 422).
        InsufficientStockError: Если остатка не хватило хотя бы на одну
            позицию (транслируется в HTTP 409; транзакция откатывается).
    """
    return await service.reserve(data.order_id, data.items)


@router.post(
    "/release",
    response_model=StockOperationResult,
    status_code=status.HTTP_200_OK,
)
async def release_stock(
    data: StockReleaseRequest,
    service: StockService = Depends(get_stock_service),
) -> StockOperationResult:
    """Возвращает на склад остаток, ранее списанный под заказ.

    Всегда отвечает 200, в том числе на повтор и на неизвестный
    `order_id`: компенсирующий вызов из orders_service делается вслепую,
    когда исход резерва неизвестен, и не должен получать ошибку за то,
    что резервировать было нечего.

    Args:
        data: Идентификатор заказа для возврата.
        service: Сервис складских операций.

    Returns:
        Результат операции с флагом `already_applied`.
    """
    return await service.release(data.order_id)


@router.post(
    "/prices",
    response_model=CartQuoteListOut,
    status_code=status.HTTP_200_OK,
)
async def quote_prices(
    data: CartQuoteRequest,
    service: CatalogService = Depends(get_catalog_service),
) -> CartQuoteListOut:
    """Считает цены корзины со скидками, не трогая остатки.

    Вызывается orders_service перед резервом: возвращённые здесь
    названия, артикулы и цены копируются в позиции заказа. Также
    используется фронтом для превью корзины.

    Args:
        data: Позиции корзины с количествами.
        service: Сервис витрины (единственное место расчёта скидок).

    Returns:
        По одной строке на каждую запрошенную позицию, включая
        недоступные товары (`is_available=False`).
    """
    quotes = await service.quote_cart(
        {item.product_id: item.quantity for item in data.items}
    )
    return CartQuoteListOut(items=[CartQuoteOut(**quote._asdict()) for quote in quotes])