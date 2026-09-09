# orders_service/app/db/database.py
"""Async-подключение к БД orders_service: engine, session maker, Depends,
а также ожидание готовности БД при старте приложения (wait_for_db).

Модуль почти идентичен products_service/app/db/database.py — общего пакета
между сервисами в проекте нет (см. project_structure), поэтому дублирование
здесь намеренное, а не оплошность.
"""

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
    """Общий декларативный базовый класс для всех ORM-моделей сервиса."""

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


async def wait_for_db() -> None:
    """Дожидается готовности БД при старте приложения, циклом с паузой.

    Делает settings.db_connect_attempts попыток выполнить `SELECT 1`
    с паузой settings.db_connect_delay секунд между ними. Каждая попытка
    логируется с номером. Ловятся OSError и sqlalchemy.exc.DBAPIError.
    Если после последней попытки соединение так и не удалось — падает
    с понятным исключением.

    Проверяется только своя БД (lamp_orders). Доступность products_service
    сюда не входит: между сервисами приложения `depends_on` нет вовсе —
    недоступность products_service обрабатывается в момент запроса на
    оформление заказа, а не при старте (см. domain_decisions).

    Raises:
        RuntimeError: Если БД не стала доступна за отведённое число попыток.
    """
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
        f"Не удалось подключиться к БД orders_service за "
        f"{settings.db_connect_attempts} попыток. Последняя ошибка: {last_error}"
    )