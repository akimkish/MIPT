"""Фабрики тестовых данных admin_service."""

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
    """Собирает несохранённый ORM-объект `Admin` с валидными значениями по умолчанию.

    Пароль хешируется настоящим `hash_password` — тесты логина проверяют
    полный цикл bcrypt, а не заглушку с равенством строк.

    Args:
        email: Email администратора; при отсутствии генерируется уникальный.
        password: Пароль в открытом виде, из которого считается хеш.
        role_name: Роль администратора.
        is_active: Флаг активности.
        **overrides: Прямая перезапись любых прочих полей модели
            (например, `failed_login_attempts=3`, `locked_until=...`).

    Returns:
        Несохранённый в сессии объект `Admin`.
    """
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
    """Создаёт и сохраняет администратора, возвращает его вместе с открытым паролем.

    Открытый пароль нужен отдельно от объекта: `Admin.password_hash` уже
    необратимо захеширован, а тестам логина требуется исходная строка.

    Args:
        session: Сессия текущего теста.
        password: Пароль в открытом виде.
        **kwargs: Прочие поля, см. `build_admin`.

    Returns:
        Кортеж (сохранённый администратор, пароль в открытом виде).
    """
    admin = build_admin(password=password, **kwargs)
    session.add(admin)
    await session.flush()
    await session.refresh(admin)
    return admin, password


def auth_headers(admin: Admin) -> dict[str, str]:
    """Собирает заголовок `Authorization` с валидным токеном для администратора.

    Args:
        admin: Администратор, на которого выписывается токен.

    Returns:
        Словарь с одним заголовком `Authorization: Bearer <token>`.
    """
    token = create_access_token(admin)
    return {"Authorization": f"Bearer {token}"}
