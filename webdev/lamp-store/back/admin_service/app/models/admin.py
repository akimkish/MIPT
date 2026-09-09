"""ORM-модель администратора admin_service."""

import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.enums import RoleName


class Admin(Base):
    """Учётная запись администратора панели управления.

    Роль хранится строкой (`role_name`), а не FK на справочник ролей:
    единственный источник истины по правам — словарь `ROLE_PERMISSIONS`
    в коде сервиса (core/roles.py). Список допустимых ролей продублирован
    здесь в CHECK-ограничении и в `RoleName`; отдельной таблицы `roles`
    в проекте сознательно нет.

    Attributes:
        admin_id: Первичный ключ (UUID4), генерируется в Python.
        email: Адрес почты, уникален, хранится в нормализованном (нижнем)
            регистре — нормализация выполняется в сервисном слое, модель
            её не делает.
        password_hash: Bcrypt-хеш пароля (60 символов). Наружу из
            admin_service не отдаётся ни при каких обстоятельствах.
        full_name: Отображаемое имя администратора.
        role_name: Роль администратора, значение из `RoleName`.
        is_active: Флаг активности учётной записи. Деактивированный админ
            не может пройти `/auth/login`, но уже выданный JWT остаётся
            валиден до истечения TTL.
        failed_login_attempts: Счётчик подряд идущих неудачных входов,
            обнуляется при успешном логине.
        locked_until: Момент, до которого учётная запись заблокирована
            после серии неудачных входов; `None`, если блокировки нет.
        last_login: Момент последнего успешного входа; `None` до первого
            входа.
        created_at: Момент создания записи.
        updated_at: Момент последнего обновления записи.
    """

    __tablename__ = "admins"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(60), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_name: Mapped[RoleName] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    last_login: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "failed_login_attempts >= 0", name="failed_login_attempts_non_negative"
        ),
        CheckConstraint(
            "role_name IN ('superadmin','manager','moderator')",
            name="role_name_allowed",
        ),
        Index("ix_admins_role_name", "role_name"),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return (
            f"Admin(id={self.admin_id!r}, email={self.email!r}, "
            f"role={self.role_name!r})"
        )