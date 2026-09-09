"""Обработчики доменных исключений: перевод в HTTP-ответы.

Роуты не оборачивают вызовы сервисов в `try/except` — исключения из
`services/exceptions.py` перехватываются здесь, централизованно, для
всего приложения. Это и держит роуты тонкими, и гарантирует одинаковый
формат ошибки для одного и того же типа проблемы во всех эндпоинтах.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.exceptions import (
    ConflictError,
    DomainError,
    DomainValidationError,
    InsufficientStockError,
    NotFoundError,
)


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики доменных исключений в приложении.

    Порядок регистрации важен: FastAPI выбирает наиболее специфичный
    зарегистрированный тип, поэтому обработчик `DomainError` (базового
    класса) можно регистрировать в любом месте — это универсальный
    fallback на случай исключения, для которого не завели отдельный
    статус-код.

    Args:
        app: Экземпляр приложения FastAPI.
    """

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        """Возвращает 404 для отсутствующих сущностей."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @app.exception_handler(ConflictError)
    async def handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:
        """Возвращает 409 при нарушении уникальности или состояния."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
        )

    @app.exception_handler(InsufficientStockError)
    async def handle_insufficient_stock(
        _: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        """Возвращает 409 с подробностями о нехватке остатка."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "product_id": str(exc.product_id),
                "requested": exc.requested,
                "available": exc.available,
            },
        )

    @app.exception_handler(DomainValidationError)
    async def handle_domain_validation(
        _: Request, exc: DomainValidationError
    ) -> JSONResponse:
        """Возвращает 422 для нарушений бизнес-правил."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        """Возвращает 400 для любых доменных ошибок без отдельного статуса."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )