"""Async-подключение к БД products_service: engine, session maker, Depends."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий декларативный базовый класс для всех ORM-моделей сервиса."""


settings = get_settings()

# pool_pre_ping: лёгкая проверка соединения перед выдачей из пула.
# wait_for_db.py (отдельный модуль) гарантирует готовность БД только на
# старте сервиса; pool_pre_ping защищает уже работающий сервис от
# протухших соединений, если Postgres перезапустят на ходу.
engine = create_async_engine(
    settings.database_url, echo=settings.sql_echo, pool_pre_ping=True
)

async_session_factory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Отдаёт сессию БД на время обработки одного HTTP-запроса.

    При исключении в обработчике делает rollback явно, не полагаясь на
    неявное поведение `Session.close()` внутри `async with` — так
    намерение видно прямо в коде. Закрытие сессии по завершении запроса
    берёт на себя внешний `async with`.

    Yields:
        Открытая асинхронная сессия SQLAlchemy.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
