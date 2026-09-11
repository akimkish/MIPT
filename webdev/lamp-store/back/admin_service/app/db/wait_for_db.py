from __future__ import annotations

import asyncio
import logging
import sys

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings
from app.db.database import engine

logger = logging.getLogger(__name__)


async def wait_for_db() -> None:
    """Ждёт готовности БД, выполняя `SELECT 1` в цикле.

    Raises:
        RuntimeError: Если БД не ответила за отведённое число попыток.
            Исключение валит контейнер намеренно: запускать миграции
            и приложение поверх недоступной БД бессмысленно.
    """
    settings = get_settings()
    last_error: Exception | None = None

    for attempt in range(1, settings.db_connect_attempts + 1):
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
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
        else:
            logger.info("Подключение к БД установлено (попытка %d)", attempt)
            return

    raise RuntimeError(
        f"Не удалось подключиться к БД orders_service за "
        f"{settings.db_connect_attempts} попыток. Последняя ошибка: {last_error}"
    )


def main() -> None:
    """Точка входа для `python -m app.db.wait_for_db`."""
    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        asyncio.run(wait_for_db())
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()