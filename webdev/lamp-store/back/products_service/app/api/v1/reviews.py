"""Публичные и административные эндпоинты отзывов."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_review_service
from app.core.permissions import Permission
from app.core.security import require_permission
from app.schemas.common import PaginatedResponse
from app.schemas.review import ReviewCreate, ReviewModerate, ReviewRead
from app.services.review import ReviewService

router = APIRouter(prefix="/products/{product_id}/reviews", tags=["reviews"])
admin_router = APIRouter(prefix="/admin/reviews", tags=["admin:reviews"])


@router.get("", response_model=PaginatedResponse[ReviewRead])
async def list_reviews(
    product_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[ReviewRead]:
    """Возвращает страницу опубликованных отзывов на товар.

    Args:
        product_id: Идентификатор товара.
        service: Сервис отзывов.
        limit: Размер страницы.
        offset: Смещение от начала выборки.

    Returns:
        Страницу отзывов с общим количеством.

    Raises:
        NotFoundError: Если товар не найден (транслируется в 404).
    """
    items, total = await service.list_for_product(
        product_id, only_approved=True, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[ReviewRead.model_validate(r) for r in items], total=total
    )


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    product_id: uuid.UUID,
    data: ReviewCreate,
    service: ReviewService = Depends(get_review_service),
) -> ReviewRead:
    """Оставляет отзыв на товар (без аутентификации — аккаунтов покупателей нет).

    Args:
        product_id: Идентификатор товара из пути; должен совпадать с
            `product_id` в теле запроса (проверка ниже).
        data: Данные отзыва.
        service: Сервис отзывов.

    Returns:
        Созданный отзыв со статусом «на модерации».

    Raises:
        NotFoundError: Если товар не найден или скрыт с витрины.
        ConflictError: Если автор уже оставлял отзыв на этот товар.
        DomainValidationError: Если `product_id` в пути и в теле не совпадают.
    """
    if data.product_id != product_id:
        from app.services.exceptions import DomainValidationError

        raise DomainValidationError(
            "product_id в пути и в теле запроса должны совпадать"
        )
    review = await service.create(data)
    return ReviewRead.model_validate(review)


@admin_router.get("", response_model=PaginatedResponse[ReviewRead])
async def admin_list_reviews_for_product(
    product_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _claims: dict = Depends(require_permission(Permission.MODERATE_REVIEWS)),
) -> PaginatedResponse[ReviewRead]:
    """Возвращает страницу всех отзывов на товар, включая неопубликованные.

    Args:
        product_id: Идентификатор товара (передаётся query-параметром,
            так как путь зарезервирован под `/admin/reviews/{review_id}`).
        service: Сервис отзывов.
        limit: Размер страницы.
        offset: Смещение от начала выборки.
        _claims: Проверенные claims администратора.

    Returns:
        Страницу отзывов с общим количеством.
    """
    items, total = await service.list_for_product(
        product_id, only_approved=False, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[ReviewRead.model_validate(r) for r in items], total=total
    )


@admin_router.patch("/{review_id}", response_model=ReviewRead)
async def moderate_review(
    review_id: uuid.UUID,
    data: ReviewModerate,
    service: ReviewService = Depends(get_review_service),
    _claims: dict = Depends(require_permission(Permission.MODERATE_REVIEWS)),
) -> ReviewRead:
    """Публикует отзыв или снимает его с публикации.

    Args:
        review_id: Идентификатор отзыва.
        data: Новое значение флага публикации.
        service: Сервис отзывов.
        _claims: Проверенные claims администратора.

    Returns:
        Обновлённый отзыв.
    """
    review = await service.set_approved(review_id, data.is_approved)
    return ReviewRead.model_validate(review)


@admin_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service),
    _claims: dict = Depends(require_permission(Permission.MODERATE_REVIEWS)),
) -> None:
    """Физически удаляет отзыв (модерация спама/оскорблений).

    Args:
        review_id: Идентификатор отзыва.
        service: Сервис отзывов.
        _claims: Проверенные claims администратора.
    """
    await service.delete(review_id)