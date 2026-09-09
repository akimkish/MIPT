"""Pydantic-схемы администратора."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleName


class AdminBase(BaseModel):
    """Поля администратора, общие для создания и чтения.

    Attributes:
        email: Адрес почты. Нормализация в нижний регистр выполняется в
            сервисном слое перед сохранением/поиском — схема этого не
            делает, чтобы не дублировать бизнес-правило в двух местах.
        full_name: Отображаемое имя администратора.
    """

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class AdminCreate(AdminBase):
    """Данные для создания администратора.

    Attributes:
        password: Пароль в открытом виде — существует только на входе в
            этот эндпоинт, до вызова `core/security.py:hash_password`.
            Дальше в системе живёт только `password_hash`.
        role_name: Роль новой учётной записи. Что создание админов
            доступно только superadmin — проверяется в api-слое, не тут.
    """

    password: str = Field(..., min_length=8, max_length=128)
    role_name: RoleName


class AdminUpdate(BaseModel):
    """Данные для частичного обновления администратора (PATCH).

    `role_name` и `password` сюда намеренно не входят: смена роли —
    отдельное действие с собственным аудитом (см. `AdminRoleUpdate`),
    а смена пароля вне контракта текущего шага.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class AdminRoleUpdate(BaseModel):
    """Данные для смены роли администратора.

    Отдельная схема, а не поле в `AdminUpdate`: по домену смену роли
    выполняет только superadmin, и она пишется в `audit_log` с
    `action='role_changed'` и `payload={old_role, new_role}` — это
    самостоятельная операция, а не часть обычного PATCH.
    """

    new_role: RoleName


class AdminRead(AdminBase):
    """Администратор в ответах API. Не содержит `password_hash`."""

    model_config = ConfigDict(from_attributes=True)

    admin_id: uuid.UUID
    role_name: RoleName
    is_active: bool
    failed_login_attempts: int
    locked_until: datetime | None
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminInDB(AdminRead):
    """Администратор с `password_hash` — только для repositories/services.

    Никогда не возвращается из api-слоя: домен явно требует, чтобы
    `password_hash` не покидал admin_service (схемы AdminCreate /
    AdminRead / AdminInDB — три отдельные, а не одна с опциональным
    полем, чтобы про этот запрет было невозможно забыть в сериализаторе).
    """

    password_hash: str