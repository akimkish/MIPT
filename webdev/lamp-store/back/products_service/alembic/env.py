# products_service/alembic/env.py
"""Async-совместимый env.py для Alembic: конфиг берётся из Settings,
метаданные — из app.db.base (моделей пока нет, но Base.metadata уже
готов их подхватить, когда они появятся на Этапе 4).
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()

# URL берём из Settings, а не из alembic.ini — единственный источник истины
# про подключение к БД совпадает с тем, что использует само приложение.
config.set_main_option("sqlalchemy.url", str(settings.database_url))

# На Этапе 4 здесь появятся реальные модели (импортом в app/db/base.py),
# autogenerate начнёт видеть их сразу, без правок этого файла.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Генерирует SQL миграций без реального подключения к БД.

    Используется, когда нужно получить .sql-файл для ручного применения
    (например, DBA-процессом), а не выполнять миграцию из процесса Alembic.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Синхронная часть применения миграций, вызывается через run_sync.

    Args:
        connection: Синхронное представление соединения, которое Alembic
            получает через AsyncConnection.run_sync().
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Применяет миграции к реально работающей БД через async engine.

    Alembic API синхронный, поэтому реальный запуск миграций оборачивается
    в connection.run_sync(), а async-часть — только открытие/закрытие
    соединения на async-движке (тот же движок, что и в приложении).
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
