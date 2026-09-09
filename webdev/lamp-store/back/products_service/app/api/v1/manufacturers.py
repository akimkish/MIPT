"""Публичные и административные эндпоинты производителей.

Структура полностью повторяет `categories.py` — обе сущности простые
справочники с одинаковым набором операций.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_manufacturer_service
from app.core.permissions import Permission
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse
from app.schemas.manufacturer import (
    ManufacturerCreate,
    ManufacturerRead,
    ManufacturerUpdate,
)
from app.services.manufacturer import ManufacturerService

router = APIRouter(prefix="/manufacturers", tags=["manufacturers"])
admin_router = APIRouter(prefix="/admin/manufacturers", tags=["admin:manufacturers"])


@router.get("", response_model=PaginatedResponse[ManufacturerRead])
async def list_manufacturers(
    service: ManufacturerService = Depends(get_manufacturer_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[ManufacturerRead]:
    """Возвращает страницу активных производителей для витрины."""
    items, total = await service.list_manufacturers(
        only_active=True, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[ManufacturerRead.model_validate(m) for m in items], total=total
    )


@admin_router.get("", response_model=PaginatedResponse[ManufacturerRead])
async def admin_list_manufacturers(
    service: ManufacturerService = Depends(get_manufacturer_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _claims: dict = Depends(require_permission(Permission.MANAGE_MANUFACTURERS)),
) -> PaginatedResponse[ManufacturerRead]:
    """Возвращает страницу всех производителей, включая скрытых."""
    items, total = await service.list_manufacturers(
        only_active=False, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[ManufacturerRead.model_validate(m) for m in items], total=total
    )


@admin_router.post(
    "", response_model=ManufacturerRead, status_code=status.HTTP_201_CREATED
)
async def create_manufacturer(
    data: ManufacturerCreate,
    service: ManufacturerService = Depends(get_manufacturer_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_MANUFACTURERS)),
) -> ManufacturerRead:
    """Создаёт нового производителя."""
    manufacturer = await service.create(data)
    return ManufacturerRead.model_validate(manufacturer)


@admin_router.patch("/{manufacturer_id}", response_model=ManufacturerRead)
async def update_manufacturer(
    manufacturer_id: uuid.UUID,
    data: ManufacturerUpdate,
    service: ManufacturerService = Depends(get_manufacturer_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_MANUFACTURERS)),
) -> ManufacturerRead:
    """Частично обновляет производителя."""
    manufacturer = await service.update(manufacturer_id, data)
    return ManufacturerRead.model_validate(manufacturer)


@admin_router.delete("/{manufacturer_id}", response_model=ManufacturerRead)
async def deactivate_manufacturer(
    manufacturer_id: uuid.UUID,
    service: ManufacturerService = Depends(get_manufacturer_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_MANUFACTURERS)),
) -> ManufacturerRead:
    """Скрывает производителя с витрины."""
    manufacturer = await service.deactivate(manufacturer_id)
    return ManufacturerRead.model_validate(manufacturer)