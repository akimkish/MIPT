import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.enums import AuditAction


class AuditLog(Base):
    """Запись журнала аудита. Только добавление — обновления и удаления нет.
    Attributes:
        log_id: Первичный ключ (UUID4), генерируется в Python.
        admin_id: Администратор — инициатор действия; `None`, если его
            не удалось сопоставить с существующей учётной записью.
        actor_email: Email, под которым пытались действовать —
            сохраняется всегда, даже если `admin_id` не определён.
        action: Тип события.
        entity_type: Тип затронутой сущности (например, `"admin"`).
        entity_id: Идентификатор затронутой сущности.
        payload: Дополнительные детали события в свободной форме
            (например, `{"old_role": ..., "new_role": ...}`).
        ip_address: IP-адрес источника запроса, если известен.
        created_at: Момент события.
    """

    __tablename__ = "audit_log"

    log_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    admin_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("admins.admin_id", ondelete="RESTRICT"),
        nullable=True,
    )
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[AuditAction] = mapped_column(String(30), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('login_success','login_failed','admin_created',"
            "'admin_deactivated','role_changed')",
            name="action_allowed",
        ),
        Index("ix_audit_log_admin_id_created_at", "admin_id", "created_at"),
        Index("ix_audit_log_action_created_at", "action", "created_at"),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return f"AuditLog(id={self.log_id!r}, action={self.action!r})"
