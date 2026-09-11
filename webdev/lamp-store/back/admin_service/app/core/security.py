from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.roles import get_permissions_for_role
from app.models.admin import Admin
from app.models.enums import RoleName
from app.services.exceptions import AuthenticationError

_BCRYPT_ROUNDS = 12


class TokenPayload(BaseModel):
    """Полезная нагрузка JWT после успешной валидации.

    Attributes:
        admin_id: Идентификатор администратора (`sub` токена).
        email: Email администратора на момент выпуска токена.
        role_name: Роль администратора на момент выпуска токена.
        jti: Идентификатор токена.
    """

    admin_id: uuid.UUID
    email: str
    role_name: RoleName
    jti: uuid.UUID


def hash_password(plain_password: str) -> str:
    """Хеширует пароль администратора алгоритмом bcrypt.

    Args:
        plain_password: Пароль в открытом виде.

    Returns:
        Bcrypt-хеш длиной 60 символов для `admins.password_hash`.
    """
    hashed = bcrypt.hashpw(
        plain_password.encode("utf-8"), bcrypt.gensalt(_BCRYPT_ROUNDS)
    )
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверяет пароль против сохранённого bcrypt-хеша.

    Args:
        plain_password: Пароль в открытом виде из формы входа.
        password_hash: Хеш из `admins.password_hash`.

    Returns:
        True, если пароль совпадает с хешем.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(admin: Admin) -> str:
    """Выпускает access-токен для администратора.

    Args:
        admin: Администратор, для которого выпускается токен.

    Returns:
        Подписанный приватным ключом JWT (RS256).
    """
    settings = get_settings()
    now = datetime.now(UTC)
    role_name = str(admin.role_name)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": str(admin.admin_id),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "email": admin.email,
        "role": role_name,
        "permissions": get_permissions_for_role(role_name),
    }
    return jwt.encode(
        payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> TokenPayload:
    """Валидирует и разбирает собственный access-токен.

    Args:
        token: JWT из заголовка `Authorization: Bearer <token>`.

    Returns:
        Разобранную полезную нагрузку токена.

    Raises:
        AuthenticationError: Токен невалиден, просрочен или не содержит
            обязательных claims.
    """
    settings = get_settings()
    try:
        raw = jwt.decode(
            token,
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            leeway=settings.jwt_leeway_seconds,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Невалидный или просроченный токен") from exc

    return TokenPayload(
        admin_id=uuid.UUID(raw["sub"]),
        email=raw["email"],
        role_name=RoleName(raw["role"]),
        jti=uuid.UUID(raw["jti"]),
    )