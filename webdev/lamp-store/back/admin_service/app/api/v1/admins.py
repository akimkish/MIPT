"""CRUD-эндпоинты управления администраторами (доступны только superadmin)."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_admin_service, require_role
from app.models.admin import Admin
from app.models.enums import RoleName
from app.schemas.admin import AdminCreate, AdminRead, AdminRoleUpdate, AdminUpdate
from app.schemas.common import PaginatedResponse
from app.services.admin import AdminService

router = APIRouter(prefix="/admins", tags=["admins"])

# Собран один раз на модуль: все эндпоинты этого роутера требуют одну
# и ту же роль, отдельный require_role(...) на каждый маршрут был бы
# просто повторением одного и того же вызова.
_require_superadmin = require_role(RoleName.SUPERADMIN)


@router.get(
    "",
    response_model=PaginatedResponse[AdminRead],
    summary="Список администраторов",
    description="Постраничный список всех учётных записей администраторов.",
)
async def list_admins(
    service: AdminService = Depends(get_admin_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _actor: Admin = Depends(_require_superadmin),
) -> PaginatedResponse[AdminRead]:
    """Возвращает страницу администраторов.

    Args:
        service: Сервис управления администраторами.
        limit: Размер страницы.
        offset: Смещение от начала выборки.
        _actor: Аутентифицированный superadmin — параметр нужен только
            для проверки доступа зависимостью, в теле не используется.

    Returns:
        Страницу администраторов с общим количеством.
    """
    items, total = await service.list_admins(limit=limit, offset=offset)
    return PaginatedResponse(
        items=[AdminRead.model_validate(a) for a in items], total=total
    )


@router.get(
    "/{admin_id}",
    response_model=AdminRead,
    summary="Карточка администратора",
    responses={404: {"description": "Администратор не найден"}},
)
async def get_admin(
    admin_id: uuid.UUID,
    service: AdminService = Depends(get_admin_service),
    _actor: Admin = Depends(_require_superadmin),
) -> AdminRead:
    """Возвращает администратора по идентификатору.

    Args:
        admin_id: Идентификатор администратора.
        service: Сервис управления администраторами.
        _actor: Аутентифицированный superadmin.

    Returns:
        Карточка администратора.

    Raises:
        NotFoundError: Если администратор не найден (HTTP 404).
    """
    admin = await service.get(admin_id)
    return AdminRead.model_validate(admin)


@router.post(
    "",
    response_model=AdminRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать администратора",
    responses={409: {"description": "Email уже используется"}},
)
async def create_admin(
    data: AdminCreate,
    service: AdminService = Depends(get_admin_service),
    actor: Admin = Depends(_require_superadmin),
) -> AdminRead:
    """Создаёт учётную запись администратора.

    Args:
        data: Данные новой учётной записи, включая роль и пароль.
        service: Сервис управления администраторами.
        actor: Superadmin, выполняющий создание — записывается в
            `audit_log` как инициатор события `admin_created`.

    Returns:
        Созданный администратор.

    Raises:
        ConflictError: Если email уже занят (HTTP 409).
    """
    admin = await service.create(data, actor=actor)
    return AdminRead.model_validate(admin)


@router.patch(
    "/{admin_id}",
    response_model=AdminRead,
    summary="Обновить данные администратора",
    description=(
        "Меняет только `full_name`/`is_active`-независимые поля. Смена "
        "роли и деактивация — отдельные аудируемые эндпоинты ниже."
    ),
    responses={404: {"description": "Администратор не найден"}},
)
async def update_admin(
    admin_id: uuid.UUID,
    data: AdminUpdate,
    service: AdminService = Depends(get_admin_service),
    _actor: Admin = Depends(_require_superadmin),
) -> AdminRead:
    """Обновляет неаудируемые поля администратора.

    Args:
        admin_id: Идентификатор администратора.
        data: Изменяемые поля (`full_name`).
        service: Сервис управления администраторами.
        _actor: Аутентифицированный superadmin.

    Returns:
        Обновлённый администратор.

    Raises:
        NotFoundError: Если администратор не найден (HTTP 404).
    """
    admin = await service.update(admin_id, data)
    return AdminRead.model_validate(admin)


@router.delete(
    "/{admin_id}",
    response_model=AdminRead,
    summary="Деактивировать администратора",
    description=(
        "Физическое удаление запрещено доменом — только `is_active=false`. "
        "Уже выданный токен деактивированного администратора остаётся "
        "валиден до истечения TTL (осознанное упрощение проекта, "
        "денилиста токенов нет)."
    ),
    responses={404: {"description": "Администратор не найден"}},
)
async def deactivate_admin(
    admin_id: uuid.UUID,
    service: AdminService = Depends(get_admin_service),
    actor: Admin = Depends(_require_superadmin),
) -> AdminRead:
    """Деактивирует учётную запись администратора.

    Args:
        admin_id: Идентификатор администратора.
        service: Сервис управления администраторами.
        actor: Superadmin, выполняющий деактивацию — записывается в
            `audit_log` как инициатор события `admin_deactivated`.

    Returns:
        Деактивированный администратор.

    Raises:
        NotFoundError: Если администратор не найден (HTTP 404).
    """
    admin = await service.deactivate(admin_id, actor=actor)
    return AdminRead.model_validate(admin)


@router.post(
    "/{admin_id}/role",
    response_model=AdminRead,
    summary="Сменить роль администратора",
    description="Событие записывается в audit_log с action='role_changed'.",
    responses={404: {"description": "Администратор не найден"}},
)
async def change_admin_role(
    admin_id: uuid.UUID,
    data: AdminRoleUpdate,
    service: AdminService = Depends(get_admin_service),
    actor: Admin = Depends(_require_superadmin),
) -> AdminRead:
    """Меняет роль администратора.

    Args:
        admin_id: Идентификатор администратора, чья роль меняется.
        data: Новая роль.
        service: Сервис управления администраторами.
        actor: Superadmin, выполняющий смену роли — записывается в
            `audit_log` вместе со старым и новым значением роли.

    Returns:
        Администратор с обновлённой ролью.

    Raises:
        NotFoundError: Если администратор не найден (HTTP 404).
    """
    admin = await service.change_role(admin_id, data.new_role, actor=actor)
    return AdminRead.model_validate(admin)