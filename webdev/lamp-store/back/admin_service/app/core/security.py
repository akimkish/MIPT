"""Хеширование паролей и работа с JWT-токенами.

Формат токена соответствует INTEGRATION_CONTRACT.md → auth_contract:
`permissions` собирается при выпуске токена из
`core/roles.py:ROLE_PERMISSIONS[role_name]`. products_service и
orders_service сравнивают эти строки со своими константами `Permission`
и ничего не знают про роли — появление новой роли требует правки только
`RoleName` + CHECK-ограничения + `ROLE_PERMISSIONS`, без изменений в
других сервисах.
"""
from app.core.roles import get_permissions_for_role

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import BaseModel

from app.core.config import Settings
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
        jti: Идентификатор токена. Не используется для денилиста сейчас
            (см. security-чек-лист), но формат заложен на будущее.
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

    `bcrypt.checkpw` сравнивает хеши за постоянное время — защита от
    timing-атак заложена в саму библиотеку, отдельно реализовывать
    константное сравнение не нужно.

    Args:
        plain_password: Пароль в открытом виде из формы входа.
        password_hash: Хеш из `admins.password_hash`.

    Returns:
        `True`, если пароль совпадает с хешем.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(admin: Admin) -> str:
    """Выпускает access-токен для администратора.

    Refresh-токена нет: срок жизни токена (`settings.jwt_ttl_minutes`,
    по контракту 30 минут) — единственная граница действия выданных
    прав. Осознанное упрощение уровня учебного проекта, подробнее — в
    security-чек-листе в конце ответа.

    Args:
        admin: Администратор, для которого выпускается токен.

    Returns:
        Подписанный приватным ключом JWT (RS256).
    """
    now = datetime.now(timezone.utc)
    payload = {
        "iss": Settings.jwt_issuer,
        "aud": Settings.jwt_audience,
        "sub": str(admin.admin_id),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=Settings.jwt_ttl_minutes),
        "email": admin.email,
        "role": admin.role_name,
        # KeyError здесь — намеренное поведение при неизвестной роли,
        # см. get_permissions_for_role.
        "permissions": get_permissions_for_role(admin.role_name),
    }
    return jwt.encode(
        payload, Settings.jwt_private_key, algorithm=Settings.jwt_algorithm
    )


def decode_access_token(token: str) -> TokenPayload:
    """Валидирует и разбирает access-токен.

    Проверяются подпись, `exp`, `iss`, `aud` (штатная проверка PyJWT,
    допуск на расхождение часов — `leeway=10`, как в
    INTEGRATION_CONTRACT.md → auth_contract). `permissions` в payload
    сейчас нет — см. модульный докстринг.

    Args:
        token: JWT из заголовка `Authorization: Bearer <token>`.

    Returns:
        Разобранная полезная нагрузка токена.

    Raises:
        AuthenticationError: Если подпись неверна, токен просрочен, либо
            `iss`/`aud` не совпадают с ожидаемыми.
    """
    try:
        raw = jwt.decode(
            token,
            Settings.jwt_public_key,
            algorithms=[Settings.jwt_algorithm],
            issuer=Settings.jwt_issuer,
            audience=Settings.jwt_audience,
            leeway=10,
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Невалидный или просроченный токен") from exc

    return TokenPayload(
        admin_id=uuid.UUID(raw["sub"]),
        email=raw["email"],
        role_name=RoleName(raw["role"]),
        jti=uuid.UUID(raw["jti"]),
    )
