# orders_service/app/core/security.py
"""Проверка JWT, выпущенного admin_service, и контроль прав доступа.

Сервис не обращается к admin_service по сети: подпись проверяется локально
публичным ключом (RS256). Приватный ключ есть только у admin_service, поэтому
подделать токен на стороне products_service/orders_service невозможно.

Файл продублирован в products_service и orders_service без изменений.
"""

from __future__ import annotations

import base64
import logging
from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.core.permissions import Permission

logger = logging.getLogger(__name__)

# auto_error=False: при отсутствии заголовка FastAPI вернул бы 403 со своим
# телом ответа, а нам нужен 401 в общем конверте {"code", "message", "details"}.
_bearer_scheme = HTTPBearer(auto_error=False, description="JWT из admin_service")

_ALGORITHM = "RS256"


class CurrentAdmin(BaseModel):
    """Админ, распознанный из JWT. В БД сервиса такой сущности нет."""

    model_config = ConfigDict(frozen=True)

    admin_id: UUID
    email: str
    role: str
    permissions: frozenset[str]

    def has_permission(self, permission: Permission) -> bool:
        """Проверяет наличие одного права.

        Args:
            permission: Требуемое право.

        Returns:
            True, если право есть в токене.
        """
        return permission.value in self.permissions


def _auth_error(status_code: int, code: str, message: str) -> HTTPException:
    """Собирает HTTPException в общем для проекта конверте ошибки.

    Args:
        status_code: HTTP-статус ответа.
        code: Машиночитаемый код ошибки.
        message: Человекочитаемое описание.

    Returns:
        Исключение, которое обработчик FastAPI превратит в
        {"code", "message", "details"}.
    """
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": None},
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache(maxsize=1)
def _public_key() -> str:
    """Достаёт публичный ключ из base64-переменной окружения.

    PEM хранится в base64, потому что содержит переносы строк, а .env их
    нормально не переживает.

    Returns:
        Публичный ключ в формате PEM.

    Raises:
        ValueError: Если переменная пустая или не декодируется.
    """
    raw = Settings.JWT_PUBLIC_KEY_B64
    if not raw:
        raise ValueError("JWT_PUBLIC_KEY_B64 is not configured")
    try:
        return base64.b64decode(raw).decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - конфигурационная ошибка на старте
        raise ValueError("JWT_PUBLIC_KEY_B64 is not valid base64 PEM") from exc


def decode_token(token: str) -> CurrentAdmin:
    """Проверяет подпись и обязательные claims токена.

    Проверяются: подпись, ``exp``, ``iss``, ``aud``. Допуск на расхождение
    часов между контейнерами — 10 секунд.

    Args:
        token: Строка JWT без префикса "Bearer ".

    Returns:
        Данные админа из claims.

    Raises:
        HTTPException: 401, если токен просрочен, подделан или неполон.
    """
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            _public_key(),
            algorithms=[_ALGORITHM],
            issuer=Settings.JWT_ISSUER,
            audience=Settings.JWT_AUDIENCE,
            leeway=Settings.JWT_LEEWAY_SECONDS,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED, "TOKEN_EXPIRED", "Token has expired"
        ) from exc
    except jwt.InvalidTokenError as exc:
        # Сюда попадают чужой iss/aud, битая подпись, отсутствующие claims.
        logger.warning("JWT rejected: %s", exc)
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid token"
        ) from exc

    try:
        return CurrentAdmin(
            admin_id=UUID(str(claims["sub"])),
            email=str(claims.get("email", "")),
            role=str(claims.get("role", "")),
            permissions=frozenset(claims.get("permissions") or ()),
        )
    except (KeyError, ValueError) as exc:
        logger.warning("JWT payload is malformed: %s", exc)
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid token payload"
        ) from exc


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentAdmin:
    """Зависимость: требует валидный токен, но никаких конкретных прав.

    Args:
        credentials: Заголовок Authorization, разобранный FastAPI.

    Returns:
        Данные админа из токена.

    Raises:
        HTTPException: 401, если заголовка нет или токен невалиден.
    """
    if credentials is None or not credentials.credentials:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            "NOT_AUTHENTICATED",
            "Authorization header is missing",
        )
    return decode_token(credentials.credentials)


def require_permission(
    *required: Permission,
) -> Callable[[CurrentAdmin], Awaitable[CurrentAdmin]]:
    """Фабрика зависимостей: требует ВСЕ перечисленные права.

    Использование::

        @router.post("/products", dependencies=[Depends(require_permission(
            Permission.PRODUCTS_WRITE))])

    или, если нужен сам админ в теле обработчика::

        admin: CurrentAdmin = Depends(require_permission(Permission.PRODUCTS_WRITE))

    Args:
        *required: Права, которые обязаны присутствовать в токене одновременно.

    Returns:
        Асинхронную зависимость FastAPI, возвращающую CurrentAdmin.

    Raises:
        ValueError: Если фабрику вызвали без прав (ошибка программиста, видна
            на импорте модуля, а не в рантайме).
    """
    if not required:
        raise ValueError("require_permission() needs at least one permission")

    missing_template = ", ".join(sorted(p.value for p in required))

    async def dependency(
        admin: CurrentAdmin = Depends(get_current_admin),
    ) -> CurrentAdmin:
        """Сверяет права из токена с требуемыми."""
        if not all(admin.has_permission(p) for p in required):
            logger.info(
                "Access denied for admin=%s role=%s: requires %s",
                admin.admin_id,
                admin.role,
                missing_template,
            )
            raise _auth_error(
                status.HTTP_403_FORBIDDEN,
                "PERMISSION_DENIED",
                f"Required permission(s): {missing_template}",
            )
        return admin

    return dependency