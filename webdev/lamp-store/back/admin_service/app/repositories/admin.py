"""Репозиторий доступа к таблице администраторов."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.enums import RoleName
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    """Доступ к данным администраторов.

    Специфичные для `Admin` выборки — здесь; типовой CRUD — в
    `BaseRepository`.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        super().__init__(session, Admin)

    async def get_by_email(self, email: str) -> Admin | None:
        """Возвращает администратора по email.

        Ожидает email уже в нормализованном (нижнем) регистре —
        нормализация выполняется в сервисном слое перед вызовом.

        Args:
            email: Адрес почты в нижнем регистре.

        Returns:
            Найденный администратор или `None`.
        """
        stmt = select(Admin).where(Admin.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_role(self, role_name: RoleName) -> Sequence[Admin]:
        """Возвращает всех администраторов с указанной ролью.

        Args:
            role_name: Роль для фильтрации.

        Returns:
            Список подходящих администраторов.
        """
        stmt = select(Admin).where(Admin.role_name == role_name.value)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def exists_any(self) -> bool:
        """Проверяет, есть ли в таблице хотя бы одна запись.

        Нужен при старте сервиса: первый админ создаётся только если
        таблица пуста (PROMPT_CONTEXT.md → domain_decisions).

        Returns:
            `True`, если в таблице есть хотя бы одна запись.
        """
        stmt = select(Admin.admin_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None