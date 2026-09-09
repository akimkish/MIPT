"""Маппинг доменных исключений сервисного слоя на HTTP-ответы."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.exceptions import ConflictError, NotFoundError


async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    """Преобразует `NotFoundError` в ответ 404.

    Args:
        _request: Запрос, на котором возникло исключение (не используется).
        exc: Исходное доменное исключение с текстом причины.

    Returns:
        JSON-ответ вида `{"detail": "..."}` со статусом 404.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    """Преобразует `ConflictError` в ответ 409.

    Args:
        _request: Запрос, на котором возникло исключение (не используется).
        exc: Исходное доменное исключение с текстом причины.

    Returns:
        JSON-ответ вида `{"detail": "..."}` со статусом 409.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики доменных исключений на приложении.

    Вынесено отдельной функцией, а не инлайном в `main.py`, чтобы
    список обработчиков было видно в одном месте и он был тривиально
    покрываем тестом «каждое исключение сервисного слоя даёт нужный код».

    Args:
        app: Экземпляр приложения FastAPI.
    """
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(ConflictError, conflict_handler)