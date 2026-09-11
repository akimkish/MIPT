import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.database import Base, get_session
from app.main import app as fastapi_app
from app.models.admin import Admin

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://lamp:lamp@localhost:5433/lamp_admin_test",
)


# --- Схема БД --------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """Создаёт движок тестовой БД и пересобирает схему один раз на сессию."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Даёт сессию, привязанную к одной внешней транзакции с откатом."""
    connection = await test_engine.connect()
    outer_transaction = await connection.begin()

    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    nested = await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(sync_session, transaction) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.sync_connection.begin_nested()

    yield session

    await session.close()
    await outer_transaction.rollback()
    await connection.close()


# --- JWT-ключи ---------------------------------------------------------


def _generate_rsa_keypair() -> tuple[str, str]:
    """Генерирует одноразовую пару RSA-ключей в формате PEM для тестов."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem


@pytest.fixture(scope="session")
def rsa_keypair() -> tuple[str, str]:
    """Основная пара ключей, которой реально подписывает admin_service."""
    return _generate_rsa_keypair()


@pytest.fixture(scope="session")
def wrong_rsa_keypair() -> tuple[str, str]:
    """Посторонняя пара ключей — для теста «токен подписан не тем ключом»."""
    return _generate_rsa_keypair()


@pytest.fixture(autouse=True, scope="session")
def _configure_jwt_settings(rsa_keypair: tuple[str, str]) -> None:
    """Подменяет ключи и параметры JWT в settings на тестовые."""
    private_pem, public_pem = rsa_keypair
    Settings.jwt_private_key = private_pem
    Settings.jwt_public_key = public_pem
    Settings.jwt_algorithm = "RS256"
    Settings.jwt_issuer = "admin_service"
    Settings.jwt_audience = "lamp-store"
    Settings.jwt_ttl_minutes = 30


@pytest.fixture
def make_token(rsa_keypair: tuple[str, str]):
    """Возвращает фабрику JWT для прямого конструирования «плохих» токенов."""
    default_private_key, _ = rsa_keypair

    def _make_token(
        admin: Admin,
        *,
        exp_delta: timedelta = timedelta(minutes=30),
        issuer: str = "admin_service",
        audience: str = "lamp-store",
        signing_key: str | None = None,
        extra_claims: dict | None = None,
        omit_claims: tuple[str, ...] = (),
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "iss": issuer,
            "aud": audience,
            "sub": str(admin.admin_id),
            "jti": "11111111-1111-1111-1111-111111111111",
            "iat": now,
            "exp": now + exp_delta,
            "email": admin.email,
            "role": admin.role_name,
        }
        for claim in omit_claims:
            payload.pop(claim, None)
        if extra_claims:
            payload.update(extra_claims)

        key = signing_key if signing_key is not None else default_private_key
        return jwt.encode(payload, key, algorithm="RS256")

    return _make_token


# --- FastAPI-приложение и HTTP-клиент --------------------------------------


@pytest_asyncio.fixture
async def app(db_session: AsyncSession):
    """Приложение с подменённой зависимостью сессии БД на тестовую."""

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    fastapi_app.dependency_overrides[get_session] = _override_get_session
    yield fastapi_app
    fastapi_app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    """Асинхронный HTTP-клиент поверх приложения, без реального сокета."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
