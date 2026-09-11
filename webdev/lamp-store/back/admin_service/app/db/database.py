import asyncio
import logging

from collections.abc import AsyncGenerator

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей admin_service."""


logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(
    str(settings.database_url),
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def wait_for_db() -> None:
    "Дожидается готовности БД при старте приложения, циклом с паузой."
    from sqlalchemy import text

    last_error: Exception | None = None

    for attempt in range(1, settings.db_connect_attempts + 1):
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            logger.info("Подключение к БД установлено (попытка %d)", attempt)
            return
        except (OSError, DBAPIError) as exc:
            last_error = exc
            logger.warning(
                "БД недоступна, попытка %d/%d: %s",
                attempt,
                settings.db_connect_attempts,
                exc,
            )
            if attempt < settings.db_connect_attempts:
                await asyncio.sleep(settings.db_connect_delay)

    raise RuntimeError(
        f"Не удалось подключиться к БД admin_service за "
        f"{settings.db_connect_attempts} попыток. Последняя ошибка: {last_error}"
    )
