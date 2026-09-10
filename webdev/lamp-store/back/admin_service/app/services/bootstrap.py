from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.roles import RoleName
from app.core.security import hash_password
from app.models.admin import Admin
from app.repositories.admin import AdminRepository

logger = logging.getLogger(__name__)


async def ensure_first_admin(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Создаёт суперадмина, если таблица администраторов пуста.

    Args:
        session_factory: Фабрика асинхронных сессий приложения.

    Raises:
        Ничего не пробрасывает наружу: сбой создания первого админа
        не должен мешать сервису подняться. Все проблемы уходят в лог.
    """
    email = (settings.first_admin_email or "").strip().lower()
    password = settings.first_admin_password or ""

    if not email or not password:
        logger.warning(
            "FIRST_ADMIN_EMAIL/FIRST_ADMIN_PASSWORD не заданы, "
            "создание первого администратора пропущено"
        )
        return

    async with session_factory() as session:
        repository = AdminRepository(session)

        if await repository.exists_any():
            logger.info("Администраторы уже есть, создание пропущено")
            return

        admin = Admin(
            email=email,
            password_hash=hash_password(password),
            full_name=settings.first_admin_email,
            role_name=RoleName.SUPERADMIN.value,
        )

        try:
            await repository.create(admin)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            logger.info(
                "Первый администратор создан параллельным процессом, пропускаем"
            )
            return

        # Пароль в лог не попадает никогда, даже на уровне DEBUG.
        logger.info(
            "Создан первый администратор %s с ролью %s",
            email,
            RoleName.SUPERADMIN.value,
        )
