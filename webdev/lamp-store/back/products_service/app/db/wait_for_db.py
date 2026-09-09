"""Ожидание готовности БД при старте сервиса.

Вызывается из entrypoint.sh как отдельный шаг, ДО применения миграций
Alembic (см. domain_decisions → «Старт сервиса и готовность БД» в
PROMPT_CONTEXT.md): без этого шага alembic упал бы первым при недоступной
БД с менее понятной ошибкой, а само приложение стартовало бы «успешно»
и падало на первом запросе, потому что create_async_engine не открывает
соединение сразу — пул ленив.

Модуль исполняется как `python -m app.db.wait_for_db`.
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import get_settings
from app.db.database import engine

logger = logging.getLogger(__name__)


class DatabaseNotReadyError(Exception):
    """БД не стала доступна за отведённое число попыток.

    Поднимается после исчерпания `DB_CONNECT_ATTEMPTS` — это и есть
    сигнал entrypoint.sh остановить запуск контейнера, а не продолжать
    попытку мигрировать/обслуживать запросы поверх недоступной БД.
    """


async def wait_for_db() -> None:
    """Опрашивает БД `SELECT 1` в цикле до готовности либо исчерпания попыток.

    Ловятся `OSError` (сетевые ошибки: отказ в соединении, DNS ещё не
    разрешает имя сервиса в docker-compose при холодном старте) и
    `sqlalchemy.exc.DBAPIError` (ошибки уровня драйвера/БД: например,
    Postgres поднялся, но ещё не готов принимать соединения). Любое
    другое исключение не перехватывается намеренно — оно означает
    ошибку конфигурации (неверный DSN, отсутствующий драйвер), а не
    временную недоступность БД, и должно падать сразу, а не тонуть
    в цикле повторов.

    Raises:
        DatabaseNotReadyError: Если за `DB_CONNECT_ATTEMPTS` попыток с
            паузой `DB_CONNECT_DELAY` секунд БД так и не ответила.
    """
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
    """Точка входа при запуске модуля как `python -m app.db.wait_for_db`.

    Явно закрывает пул соединений (`engine.dispose()`) по завершении —
    это отдельный короткоживущий процесс, а не сам сервис, поэтому
    держать пул открытым после него незачем. Функция `wait_for_db()`
    сама пул не закрывает: при импорте модуля из другого места (например,
    из теста) движок должен оставаться пригодным для дальнейшего
    использования тем же процессом.
    """
    try:
        await wait_for_db()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    asyncio.run(_run_as_script())
