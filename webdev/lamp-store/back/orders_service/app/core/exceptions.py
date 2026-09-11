from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.exceptions import ConflictError, NotFoundError


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


async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    """Преобразует `NotFoundError` в ответ 404.

    Args:
        _request: Запрос, на котором возникло исключение (не используется).
        exc: Исходное доменное исключение с текстом причины.

    Returns:
        Ответ 404 в едином конверте.
    """
    return error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc))


async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    """Преобразует `ConflictError` в ответ 409.

    Args:
        _request: Запрос, на котором возникло исключение (не используется).
        exc: Исходное доменное исключение с текстом причины.

    Returns:
        Ответ 409 в едином конверте.
    """
    return error_response(status.HTTP_409_CONFLICT, "CONFLICT", str(exc))


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Приводит любые `HTTPException` к единому конверту.

    Args:
        _request: Запрос, на котором возникло исключение (не используется).
        exc: Исходное исключение FastAPI/Starlette.

    Returns:
        Ответ в едином конверте с исходным статусом и заголовками.
    """
    headers = getattr(exc, "headers", None)
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code, content=exc.detail, headers=headers
        )
    return error_response(
        exc.status_code, "HTTP_ERROR", str(exc.detail), headers=headers
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Приводит ошибки валидации запроса к единому конверту.

    Args:
        _request: Запрос, на котором возникло исключение (не используется).
        exc: Исключение валидации Pydantic.

    Returns:
        Ответ 422 в едином конверте; подробности — в `details`.
    """
    return error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        "Некорректные данные запроса",
        details=exc.errors(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики исключений на приложении.

    Args:
        app: Экземпляр приложения FastAPI.
    """
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(ConflictError, conflict_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
