"""Административные эндпоинты промо-акций.

Публичного листинга акций нет: покупатель видит их влияние через
`display_price`/`bulk_discount_hint` в карточке товара, а не список
акций как таковой.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_promo_service
from app.core.permissions import Permission
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse
from app.schemas.promo import PromoCreate, PromoRead, PromoUpdate
from app.services.promo import PromoService

admin_router = APIRouter(prefix="/admin/promos", tags=["admin:promos"])


@admin_router.get("", response_model=PaginatedResponse[PromoRead])
async def list_promos_for_product(
    product_id: uuid.UUID = Query(...),
    service: PromoService = Depends(get_promo_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PROMOS)),
) -> PaginatedResponse[PromoRead]:
    """Возвращает страницу всех акций товара, включая выключенные.

    Args:
        product_id: Идентификатор товара.
        service: Сервис акций.
        limit: Размер страницы.
        offset: Смещение от начала выборки.
        _claims: Проверенные claims администратора.

    Returns:
        Страницу акций с общим количеством.
    """
    items, total = await service.list_for_product(
        product_id, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[PromoRead.model_validate(p) for p in items], total=total
    )


@admin_router.post("", response_model=PromoRead, status_code=status.HTTP_201_CREATED)
async def create_promo(
    data: PromoCreate,
    service: PromoService = Depends(get_promo_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PROMOS)),
) -> PromoRead:
    """Создаёт акцию на товар.

    Args:
        data: Данные новой акции.
        service: Сервис акций.
        _claims: Проверенные claims администратора.

    Returns:
        Созданную акцию.
    """
    promo = await service.create(data)
    return PromoRead.model_validate(promo)


@admin_router.patch("/{promo_id}", response_model=PromoRead)
async def update_promo(
    promo_id: uuid.UUID,
    data: PromoUpdate,
    service: PromoService = Depends(get_promo_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PROMOS)),
) -> PromoRead:
    """Частично обновляет акцию.

    Args:
        promo_id: Идентификатор акции.
        data: Изменяемые поля.
        service: Сервис акций.
        _claims: Проверенные claims администратора.

    Returns:
        Обновлённую акцию.
    """
    promo = await service.update(promo_id, data)
    return PromoRead.model_validate(promo)


@admin_router.delete("/{promo_id}", response_model=PromoRead)
async def deactivate_promo(
    promo_id: uuid.UUID,
    service: PromoService = Depends(get_promo_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_PROMOS)),
) -> PromoRead:
    """Выключает акцию (физическое удаление запрещено).

    Args:
        promo_id: Идентификатор акции.
        service: Сервис акций.
        _claims: Проверенные claims администратора.

    Returns:
        Выключенную акцию.
    """
    promo = await service.deactivate(promo_id)
    return PromoRead.model_validate(promo)