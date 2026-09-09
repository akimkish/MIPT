"""Точка входа FastAPI admin_service: приложение, роутеры, обработчики ошибок."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.exceptions import resolve_error_mapping
from app.schemas.common import ErrorResponse
from app.services.exceptions import ServiceError

logger = logging.getLogger(__name__)

app = FastAPI(title="Lamp Store — Admin Service")
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    """Проверка живости сервиса без обращения к БД.

    Returns:
        Статичный ответ `{"status": "ok"}`. Поскольку uvicorn начинает
        принимать запросы только после отработки `entrypoint.sh`
        (ожидание БД + миграции), 200 здесь уже означает готовность
        сервиса — это единственный сигнал готовности для CI.
    """
    return {"status": "ok"}


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Транслирует доменные исключения сервисного слоя в единый конверт ошибки.

    Args:
        request: Запрос, на котором возникло исключение (обязателен по
            сигнатуре обработчика FastAPI, в теле ответа не используется).
        exc: Пойманное исключение сервисного слоя.

    Returns:
        JSON-ответ формата `{"code", "message", "details"}` с HTTP-
        статусом, соответствующим типу исключения.
    """
    mapping = resolve_error_mapping(exc)
    return JSONResponse(
        status_code=mapping.status_code,
        content=ErrorResponse(code=mapping.code, message=str(exc)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Приводит ошибки валидации запроса к тому же конверту ошибки.

    Без этого обработчика 422 от Pydantic/FastAPI отдавался бы в
    дефолтном формате `{"detail": [...]}`, который не совпадает с
    единым конвертом ошибки из INTEGRATION_CONTRACT.md.

    Args:
        request: Запрос с невалидным телом или параметрами.
        exc: Исключение валидации со списком ошибок по полям.

    Returns:
        JSON-ответ с кодом `VALIDATION_ERROR` и списком ошибок в `details`.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code="VALIDATION_ERROR",
            message="Ошибка валидации запроса",
            details=exc.errors(),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Ловит всё, что не является доменным исключением или ошибкой валидации.

    Тело ответа не содержит текста исходного исключения — внутренние
    детали (SQL-ошибка, путь к файлу и т.п.) не должны утекать наружу,
    тот же принцип, что и для чужих внутренних ошибок в
    INTEGRATION_CONTRACT.md. Полный traceback уходит только в лог.

    Args:
        request: Запрос, на котором возникло необработанное исключение.
        exc: Исходное исключение.

    Returns:
        JSON-ответ 500 с общим кодом `INTERNAL_ERROR` без деталей.
    """
    logger.exception("Необработанное исключение при обработке запроса", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="INTERNAL_ERROR", message="Внутренняя ошибка сервиса"
        ).model_dump(),
    )