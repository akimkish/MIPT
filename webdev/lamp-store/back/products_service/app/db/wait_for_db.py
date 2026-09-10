import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings
from app.db.database import engine

logger = logging.getLogger(__name__)


class DatabaseNotReadyError(Exception):
    pass


async def wait_for_db() -> None:
    settings = get_settings()
    attempts = settings.db_connect_attempts
    delay = settings.db_connect_delay

    for attempt in range(1, attempts + 1):
        logger.info("Попытка подключения к БД %d/%d...", attempt, attempts)
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except (OSError, DBAPIError) as exc:
            logger.warning("Попытка %d/%d не удалась: %s", attempt, attempts, exc)
            if attempt == attempts:
                raise DatabaseNotReadyError(
                    f"БД не стала доступна за {attempts} попыток "
                    f"с интервалом {delay} с"
                ) from exc
            await asyncio.sleep(delay)
        else:
            logger.info("Подключение к БД успешно установлено.")
            return


async def _run_as_script() -> None:

    try:
        await wait_for_db()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    asyncio.run(_run_as_script())
