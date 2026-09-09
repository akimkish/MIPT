"""Общие фикстуры тестов orders_service: тестовая БД, HTTP-клиент, фабрики.

ВАЖНО: переменные окружения для тестовой БД, JWT-ключей и остальных
обязательных настроек выставляются здесь ДО первого импорта модулей
приложения. `app.core.config.get_settings()` и
`app.db.database.async_session_factory` читают окружение в момент
первого вызова/импорта — если переменные не будут выставлены раньше,
сборка `Settings()` упадёт с `ValidationError` ещё на этапе сбора
тестов (pytest --collect-only), как это уже происходило.

Тестовая пара RSA-ключей генерируется один раз на процесс: приватным
ключом `make_token` подписывает тестовые токены, публичный уходит в
`JWT_PUBLIC_KEY_B64`, которым `app.core.security` реально проверяет
подпись — так тесты идут по настоящему пути RS256-проверки, а не мимо
него.
"""

import base64
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_TEST_PRIVATE_KEY_PEM = _TEST_PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")
_TEST_PUBLIC_KEY_PEM = (
    _TEST_PRIVATE_KEY.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("utf-8")
)

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://lamp:lamp@localhost:5433/lamp_orders_test",
    ),
)
os.environ.setdefault(
    "JWT_PUBLIC_KEY_B64",
    base64.b64encode(_TEST_PUBLIC_KEY_PEM.encode("utf-8")).decode("utf-8"),
)
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")
os.environ.setdefault("PRODUCTS_SERVICE_URL", "http://products_service:8000")
# JWT_ALGORITHM/JWT_ISSUER/JWT_AUDIENCE/JWT_LEEWAY_SECONDS оставлены на
# дефолтах Settings ("RS256", "admin_service", "lamp-store", 10 секунд) —
# они совпадают с auth_contract, переопределять не нужно.

import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_session
from app.core.permissions import Permission
from app.db.database import Base
from app.main import app
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.order_item import OrderItem

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


# --- База данных ------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Создаёт движок на тестовую БД и один раз накатывает схему.

    Схема создаётся напрямую через `Base.metadata.create_all`, а не
    через `alembic upgrade head`: для основной массы тестов важна сама
    структура таблиц/ограничений, а не процесс миграции. Корректность
    самой миграции (что она действительно порождает эту же схему и
    откатывается обратно) проверяется отдельно, в `test_migrations.py`.

    Yields:
        Асинхронный движок SQLAlchemy на тестовую БД.
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Даёт сессию в транзакции, откатываемой после каждого теста.

    Открывает соединение и внешнюю транзакцию на уровне connection,
    затем создаёт `AsyncSession` с `join_transaction_mode="create_savepoint"`:
    любой `session.commit()` внутри тестируемого кода (репозитории и
    сервисы вызывают его напрямую) на деле лишь освобождает вложенный
    SAVEPOINT, а не завершает внешнюю транзакцию. Поэтому данные теста
    никогда не долетают до реальной БД — откат в `finally` гарантированно
    стирает все изменения, тесты не зависят друг от друга.

    Args:
        test_engine: Движок тестовой БД (session-scoped).

    Yields:
        Сессия, привязанная к отдельной транзакции текущего теста.
    """
    connection = await test_engine.connect()
    outer_transaction = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await outer_transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Даёт асинхронный HTTP-клиент с подменённой зависимостью БД.

    Подмена `get_session` на фикстуру `db_session` — ключевой момент:
    без неё роуты открывали бы собственную сессию на реальный
    `async_session_factory`, и тестовая транзакция (см. `db_session`)
    просто не была бы видна запросам через клиент.

    Args:
        db_session: Сессия текущего теста, используемая всеми запросами.

    Yields:
        Клиент httpx, обращающийся к приложению in-process (без сети).
    """

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --- Фабрики тестовых данных -------------------------------------------


def make_order(**overrides: object) -> Order:
    """Собирает ORM-объект заказа с валидными значениями по умолчанию.

    Не добавляет объект в сессию и не делает flush — это осознанно
    оставлено вызывающему тесту, чтобы тест сам решал, когда объект
    должен реально попасть в БД (например, для проверки CHECK-ограничений
    нужен именно flush с "плохими" данными).

    Args:
        **overrides: Поля, которые нужно переопределить относительно
            значений по умолчанию.

    Returns:
        Новый ORM-объект `Order`, ещё не сохранённый в БД.
    """
    defaults: dict[str, object] = {
        "order_id": uuid.uuid4(),
        "idempotency_key": f"idem-{uuid.uuid4()}",
        "user_name": "Иван Иванов",
        "phone": "+79990000000",
        "email": "buyer@example.com",
        "delivery_address": "г. Москва, ул. Ленина, д. 1",
        "total_price": Decimal("1500.00"),
        "status": OrderStatus.NEW.value,
    }
    defaults.update(overrides)
    return Order(**defaults)


def make_order_item(order: Order, **overrides: object) -> OrderItem:
    """Собирает ORM-объект позиции заказа с валидными значениями по умолчанию.

    Args:
        order: Заказ, к которому будет привязана позиция (`order_id`
            берётся из него, если явно не переопределён).
        **overrides: Поля, которые нужно переопределить.

    Returns:
        Новый ORM-объект `OrderItem`, ещё не сохранённый в БД.
    """
    defaults: dict[str, object] = {
        "item_id": uuid.uuid4(),
        "order_id": order.order_id,
        "external_product_id": uuid.uuid4(),
        "product_name": "Лампа E27 LED 10W",
        "sku": "LMP-000001",
        "image_url": None,
        "item_quantity": 2,
        "original_unit_price": Decimal("200.00"),
        "unit_price": Decimal("180.00"),
        "promo_id": None,
        "total_price": Decimal("360.00"),
    }
    defaults.update(overrides)
    return OrderItem(**defaults)


@pytest_asyncio.fixture
async def saved_order(db_session: AsyncSession) -> Order:
    """Создаёт и сохраняет в тестовой БД заказ с одной позицией.

    Args:
        db_session: Сессия текущего теста.

    Returns:
        Сохранённый заказ с загруженной (через refresh) позицией.
    """
    order = make_order()
    db_session.add(order)
    await db_session.flush()
    item = make_order_item(order)
    db_session.add(item)
    await db_session.flush()
    await db_session.refresh(order, attribute_names=["items"])
    return order


# --- Аутентификация (RS256, claims по auth_contract) -----------------------


TokenFactory = Callable[..., str]


@pytest.fixture
def make_token() -> TokenFactory:
    """Даёт фабрику JWT-токенов (RS256), подписанных тестовым приватным ключом.

    Возвращает функцию, а не готовый токен: разным тестам нужны разные
    наборы прав, время жизни, issuer/audience и (для проверки подделки)
    другой ключ подписи — проще параметризовать вызов, чем городить
    фикстуру на каждый случай.

    Returns:
        Функция `make_token(...)`, см. сигнатуру `_make_token`.
    """

    def _make_token(
        permissions: list[Permission] | None = None,
        role: str = "manager",
        exp_delta: timedelta = timedelta(minutes=30),
        issuer: str = "admin_service",
        audience: str = "lamp-store",
        private_key_pem: str | None = None,
        extra_claims: dict[str, object] | None = None,
    ) -> str:
        """Формирует подписанный JWT с claims по auth_contract.

        Args:
            permissions: Список прав, кладётся в claim "permissions".
                По умолчанию — оба права orders_service (VIEW_ORDERS и
                MANAGE_ORDERS), этого достаточно, когда конкретное
                право не является предметом теста. Пустой список
                (`[]`) — валидный ввод для проверки отсутствия прав.
            role: Значение claim "role" (для полноты структуры токена;
                orders_service его не читает при авторизации — только
                claim "permissions", согласно auth_contract).
            exp_delta: Смещение времени истечения относительно текущего
                момента; отрицательное значение даёт уже истёкший токен.
            issuer: Значение claim "iss"; передать значение, отличное
                от "admin_service", чтобы проверить отказ по issuer.
            audience: Значение claim "aud"; аналогично issuer.
            private_key_pem: PEM приватного ключа для подписи; по
                умолчанию — тестовый ключ, соответствующий публичному
                ключу в `JWT_PUBLIC_KEY_B64`. Передача другого ключа
                имитирует токен, подписанный не admin_service.
            extra_claims: Дополнительные claims поверх стандартных
                (перезаписывают одноимённые стандартные поля).

        Returns:
            Закодированная строка JWT (RS256).
        """
        now = datetime.now(timezone.utc)
        payload: dict[str, object] = {
            "iss": issuer,
            "aud": audience,
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + exp_delta,
            "email": "admin@example.com",
            "role": role,
            "permissions": [
                p.value
                for p in (
                    permissions
                    if permissions is not None
                    else [Permission.VIEW_ORDERS, Permission.MANAGE_ORDERS]
                )
            ],
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload,
            private_key_pem or _TEST_PRIVATE_KEY_PEM,
            algorithm="RS256",
        )

    return _make_token


@pytest.fixture
def auth_headers(make_token: TokenFactory) -> Callable[..., dict[str, str]]:
    """Даёт функцию для быстрого построения заголовка `Authorization`.

    Args:
        make_token: Фабрика токенов.

    Returns:
        Функция `auth_headers(permissions=None, **kwargs) ->
        {"Authorization": "Bearer ..."}`. Без аргументов даёт токен с
        обоими правами orders_service — достаточно для happy-path
        тестов, где конкретное право не проверяется.
    """

    def _headers(
        permissions: list[Permission] | None = None, **kwargs: object
    ) -> dict[str, str]:
        token = make_token(permissions=permissions, **kwargs)
        return {"Authorization": f"Bearer {token}"}

    return _headers