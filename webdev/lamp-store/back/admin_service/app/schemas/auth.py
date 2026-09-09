"""Pydantic-схемы аутентификации."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.admin import AdminRead


class LoginRequest(BaseModel):
    """Данные формы входа."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Ответ успешного входа."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(AdminRead):
    """Ответ `/auth/me` — данные текущего администратора по токену."""