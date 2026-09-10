import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.error_handlers import register_error_handlers
from app.services.exceptions import (
    ConflictError,
    DomainError,
    DomainValidationError,
    InsufficientStockError,
    NotFoundError,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def error_app() -> FastAPI:
    """Изолированное приложение только с обработчиками ошибок — без БД и роутов."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise/not-found")
    async def _raise_not_found() -> None:
        raise NotFoundError("nope")

    @app.get("/raise/conflict")
    async def _raise_conflict() -> None:
        raise ConflictError("conflict")

    @app.get("/raise/insufficient-stock")
    async def _raise_insufficient_stock() -> None:
        import uuid

        raise InsufficientStockError(uuid.uuid4(), requested=5, available=2)

    @app.get("/raise/domain-validation")
    async def _raise_domain_validation() -> None:
        raise DomainValidationError("invalid")

    @app.get("/raise/domain-error")
    async def _raise_domain_error() -> None:
        raise DomainError("generic")

    return app


@pytest.mark.parametrize(
    ("path", "expected_status"),
    [
        ("/raise/not-found", 404),
        ("/raise/conflict", 409),
        ("/raise/insufficient-stock", 409),
        ("/raise/domain-validation", 422),
        ("/raise/domain-error", 400),
    ],
)
async def test_domain_exception_maps_to_expected_status(
    error_app: FastAPI, path: str, expected_status: int
) -> None:
    transport = ASGITransport(app=error_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    assert response.status_code == expected_status
