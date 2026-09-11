import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin import Admin
from app.models.enums import RoleName

DEFAULT_PASSWORD = "correct-horse-battery-staple"


def build_admin(
    *,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
    role_name: RoleName = RoleName.MANAGER,
    is_active: bool = True,
    **overrides: Any,
) -> Admin:

    unique = uuid.uuid4().hex[:8]
    values: dict[str, Any] = {
        "email": email or f"admin.{unique}@lampstore.dev",
        "password_hash": hash_password(password),
        "full_name": f"Test Admin {unique}",
        "role_name": role_name.value,
        "is_active": is_active,
    }
    values.update(overrides)
    return Admin(**values)


async def create_admin(
    session: AsyncSession,
    *,
    password: str = DEFAULT_PASSWORD,
    **kwargs: Any,
) -> tuple[Admin, str]:

    admin = build_admin(password=password, **kwargs)
    session.add(admin)
    await session.flush()
    await session.refresh(admin)
    return admin, password


def auth_headers(admin: Admin) -> dict[str, str]:

    token = create_access_token(admin)
    return {"Authorization": f"Bearer {token}"}
