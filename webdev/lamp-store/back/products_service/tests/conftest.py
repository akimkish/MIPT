import os
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.database import Base
from app.db.database import get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/lamp_products_test",
)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:

    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def connection(engine: AsyncEngine) -> AsyncGenerator[AsyncConnection, None]:

    async with engine.connect() as conn:
        yield conn


@pytest_asyncio.fixture
async def session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """Сессия для теста: изменения сервисов видны внутри теста, но
    полностью откатываются после него, несмотря на `commit()` в сервисах.

    `join_transaction_mode="create_savepoint"` — commit() из кода сервиса
    освобождает SAVEPOINT, а не внешнюю транзакцию `connection`; именно
    она откатывается автоматически при выходе из `async with`.
    """
    trans = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    async_session = session_factory()
    try:
        yield async_session
    finally:
        await async_session.close()
        await trans.rollback()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент FastAPI с подменённой зависимостью БД на тестовую сессию."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Аутентификация
# ---------------------------------------------------------------------------


@pytest.fixture
def make_token() -> Callable[..., str]:
    """Фабрика JWT для тестов авторизации."""
    settings = get_settings()

    def _make(
        permissions: list[str] | None = None,
        *,
        sub: str = "admin-1",
        expired: bool = False,
        bad_secret: bool = False,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": sub,
            "permissions": permissions or [],
            "iat": now,
            "exp": (
                (now - timedelta(seconds=1))
                if expired
                else (now + timedelta(minutes=15))
            ),
        }
        secret = "wrong-secret" if bad_secret else settings.jwt_secret
        return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)

    return _make


@pytest.fixture
def auth_headers(make_token: Callable[..., str]) -> Callable[[list[str]], dict]:
    """Готовый заголовок Authorization с нужным набором прав."""

    def _headers(permissions: list[str]) -> dict:
        return {"Authorization": f"Bearer {make_token(permissions)}"}

    return _headers


@pytest.fixture
def service_headers() -> dict:
    """Заголовок X-Service-Token для internal-эндпоинтов."""
    return {"X-Service-Token": get_settings().service_token}
