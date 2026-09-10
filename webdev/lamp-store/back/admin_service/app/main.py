import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.exceptions import resolve_error_mapping
from app.schemas.common import ErrorResponse
from app.services.exceptions import ServiceError
from app.services.bootstrap import ensure_first_admin
from app.db.database import async_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await ensure_first_admin(async_session_factory)
    yield


app = FastAPI(title="Lamp Store — Admin Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:

    mapping = resolve_error_mapping(exc)
    return JSONResponse(
        status_code=mapping.status_code,
        content=ErrorResponse(code=mapping.code, message=str(exc)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code="VALIDATION_ERROR",
            message="Ошибка валидации запроса",
            details=exc.errors(),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    logger.exception("Необработанное исключение при обработке запроса", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="INTERNAL_ERROR", message="Внутренняя ошибка сервиса"
        ).model_dump(),
    )
