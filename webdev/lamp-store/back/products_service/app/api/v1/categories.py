"""Публичные и административные эндпоинты категорий."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_category_service
from app.core.permissions import Permission
from app.core.security import require_permission
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import PaginatedResponse
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])
admin_router = APIRouter(prefix="/admin/categories", tags=["admin:categories"])


@router.get("", response_model=PaginatedResponse[CategoryRead])
async def list_categories(
    service: CategoryService = Depends(get_category_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[CategoryRead]:
    """Возвращает страницу активных категорий для витрины.

    Args:
        service: Сервис категорий.
        limit: Размер страницы.
        offset: Смещение от начала выборки.

    Returns:
        Страницу категорий с общим количеством.
    """
    items, total = await service.list_categories(
        only_active=True, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[CategoryRead.model_validate(c) for c in items], total=total
    )


@admin_router.get("", response_model=PaginatedResponse[CategoryRead])
async def admin_list_categories(
    service: CategoryService = Depends(get_category_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _claims: dict = Depends(require_permission(Permission.MANAGE_CATEGORIES)),
) -> PaginatedResponse[CategoryRead]:
    """Возвращает страницу всех категорий, включая скрытые (для админки).

    Args:
        service: Сервис категорий.
        limit: Размер страницы.
        offset: Смещение от начала выборки.
        _claims: Проверенные claims администратора с правом
            `manage_categories`.

    Returns:
        Страницу категорий с общим количеством.
    """
    items, total = await service.list_categories(
        only_active=False, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[CategoryRead.model_validate(c) for c in items], total=total
    )


@admin_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_CATEGORIES)),
) -> CategoryRead:
    """Создаёт новую категорию.

    Args:
        data: Данные новой категории.
        service: Сервис категорий.
        _claims: Проверенные claims администратора.

    Returns:
        Созданную категорию.
    """
    category = await service.create(data)
    return CategoryRead.model_validate(category)


@admin_router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_CATEGORIES)),
) -> CategoryRead:
    """Частично обновляет категорию.

    Args:
        category_id: Идентификатор категории.
        data: Изменяемые поля.
        service: Сервис категорий.
        _claims: Проверенные claims администратора.

    Returns:
        Обновлённую категорию.
    """
    category = await service.update(category_id, data)
    return CategoryRead.model_validate(category)


@admin_router.delete("/{category_id}", response_model=CategoryRead)
async def deactivate_category(
    category_id: uuid.UUID,
    service: CategoryService = Depends(get_category_service),
    _claims: dict = Depends(require_permission(Permission.MANAGE_CATEGORIES)),
) -> CategoryRead:
    """Скрывает категорию с витрины (физическое удаление запрещено).

    Args:
        category_id: Идентификатор категории.
        service: Сервис категорий.
        _claims: Проверенные claims администратора.

    Returns:
        Деактивированную категорию.
    """
    category = await service.deactivate(category_id)
    return CategoryRead.model_validate(category)
