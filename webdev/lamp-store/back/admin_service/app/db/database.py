# admin_service/app/db/database.py
"""Async-подключение к БД admin_service: engine, session maker, Depends,
а также ожидание готовности БД при старте приложения (wait_for_db).

Модуль структурно идентичен одноимённым файлам products_service и
orders_service — общего пакета между сервисами в проекте нет (см.
project_structure), поэтому дублирование намеренное.
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
    """Базовый класс для всех ORM-моделей admin_service."""


# Импорт моделей — ДОЛЖЕН быть в самом низу файла, после определения Base.
# Иначе Alembic autogenerate увидит пустую Base.metadata и предложит
# удалить все таблицы. Циклический импорт здесь безопасен: к моменту
# выполнения этой строки класс Base уже определён выше, так что
# `app/models/admin.py`, делая `from app.db.base import Base`, получает
# уже готовый объект, даже если модуль app.db.base ещё не доисполнился.

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

    Это тот же шаг, что и в products_service/orders_service, но здесь у
    него дополнительная цена: пока БД недоступна, бутстрап первого админа
    (см. app/db/base.py и стартовую логику приложения) выполнить нельзя —
    поэтому wait_for_db обязана отработать раньше него, а не только раньше
    Alembic.

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
        f"Не удалось подключиться к БД admin_service за "
        f"{settings.db_connect_attempts} попыток. Последняя ошибка: {last_error}"
    )
