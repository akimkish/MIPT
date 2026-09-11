from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.exceptions import (
    ConflictError,
    DomainError,
    DomainValidationError,
    InsufficientStockError,
    NotFoundError,
    ProductNotAvailableError,
)


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Собирает ответ в едином конверте ошибки.

    Args:
        status_code: HTTP-статус ответа.
        code: Машиночитаемый код ошибки.
        message: Человекочитаемое сообщение.
        details: Дополнительные данные или `None`.
        headers: Дополнительные заголовки ответа.

    Returns:
        JSON-ответ вида `{"code", "message", "details"}`.
    """
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "details": details},
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики исключений в приложении.

    Args:
        app: Экземпляр приложения FastAPI.
    """

    @app.exception_handler(ProductNotAvailableError)
    async def handle_product_not_available(
        _: Request, exc: ProductNotAvailableError
    ) -> JSONResponse:
        return error_response(
            status.HTTP_404_NOT_FOUND,
            "PRODUCT_NOT_AVAILABLE",
            str(exc),
            details={"product_id": str(exc.product_id)} if exc.product_id else None,
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        """Возвращает 404 для отсутствующих сущностей."""
        return error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc))

    @app.exception_handler(InsufficientStockError)
    async def handle_insufficient_stock(
        _: Request, exc: InsufficientStockError
    ) -> JSONResponse:
        """Возвращает 409 с подробностями о нехватке остатка."""
        return error_response(
            status.HTTP_409_CONFLICT,
            "INSUFFICIENT_STOCK",
            str(exc),
            details={
                "items": [
                    {
                        "product_id": str(exc.product_id),
                        "requested": exc.requested,
                        "available": exc.available,
                    }
                ]
            },
        )

    @app.exception_handler(ConflictError)
    async def handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:
        """Возвращает 409 при нарушении уникальности или состояния."""
        return error_response(status.HTTP_409_CONFLICT, "CONFLICT", str(exc))

    @app.exception_handler(DomainValidationError)
    async def handle_domain_validation(
        _: Request, exc: DomainValidationError
    ) -> JSONResponse:
        """Возвращает 422 для нарушений бизнес-правил."""
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "DOMAIN_VALIDATION_ERROR", str(exc)
        )

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        """Возвращает 400 для доменных ошибок без отдельного статуса."""
        return error_response(status.HTTP_400_BAD_REQUEST, "DOMAIN_ERROR", str(exc))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Приводит любые HTTPException к единому конверту.

        Если `detail` уже словарь с ключом `code` (так их формируют
        `AuthError` и `PermissionDeniedError`), он отдаётся как есть.
        """
        headers = getattr(exc, "headers", None)
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code, content=exc.detail, headers=headers
            )
        return error_response(
            exc.status_code, "HTTP_ERROR", str(exc.detail), headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Приводит ошибки валидации запроса к единому конверту."""
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Некорректные данные запроса",
            details=exc.errors(),
        )
