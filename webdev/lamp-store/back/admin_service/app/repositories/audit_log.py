"""Репозиторий журнала аудита (только добавление и чтение)."""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Доступ к журналу аудита.

    Журнал — append-only: `update`/`delete` из `BaseRepository` для
    этой сущности просто никогда не вызываются.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        super().__init__(session, AuditLog)

    async def record(
        self,
        *,
        action: AuditAction,
        actor_email: str,
        admin_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Добавляет запись в журнал аудита.

        Args:
            action: Тип события.
            actor_email: Email, под которым выполнялось действие.
            admin_id: Идентификатор администратора-инициатора, если
                известен (для `login_failed` с несуществующим email —
                `None`).
            entity_type: Тип затронутой сущности.
            entity_id: Идентификатор затронутой сущности.
            payload: Дополнительные детали события.
            ip_address: IP-адрес источника запроса.

        Returns:
            Созданная запись журнала.
        """
        entry = AuditLog(
            action=action,
            actor_email=actor_email,
            admin_id=admin_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip_address=ip_address,
        )
        return await self.create(entry)

    async def list_for_admin(self, admin_id: uuid.UUID) -> Sequence[AuditLog]:
        """Возвращает события журнала для конкретного администратора.

        Args:
            admin_id: Идентификатор администратора.

        Returns:
            Список событий в хронологическом порядке (от старых к новым).
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.admin_id == admin_id)
            .order_by(AuditLog.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()