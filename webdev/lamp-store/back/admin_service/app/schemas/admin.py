import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleName


class AdminBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class AdminCreate(AdminBase):

    password: str = Field(..., min_length=8, max_length=128)
    role_name: RoleName


class AdminUpdate(BaseModel):

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class AdminRoleUpdate(BaseModel):

    new_role: RoleName


class AdminRead(AdminBase):

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
    password_hash: str
