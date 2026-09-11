"""Проверка JWT администратора и токена service-to-service.

Токен админа проверяется локально: подпись RS256 сверяется публичным ключом
из настроек, сетевого обращения к admin_service нет ни на одном запросе.

Сервис ничего не знает о ролях: решение принимается по claim ``permissions``,
который admin_service собирает из ROLE_PERMISSIONS при выпуске токена.
"""

from __future__ import annotations

import base64
import logging
import secrets
import uuid
from collections.abc import Awaitable, Callable
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import Settings, get_settings
from app.core.permissions import Permission

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """Полезная нагрузка access-токена admin_service.

    Attributes:
        sub: Идентификатор администратора (`admins.admin_id`).
        jti: Идентификатор токена. Сейчас не используется, зарезервирован
            под возможный денилист.
        email: Email администратора в нижнем регистре.
        role: Строка `admins.role_name` как есть. Используется только для
            логов: решения по ней не принимаются.
        permissions: Строковые права, собранные из ROLE_PERMISSIONS.
        iat: Момент выпуска токена (unix timestamp).
        exp: Момент истечения токена (unix timestamp).
    """

    model_config = ConfigDict(extra="ignore")

    sub: uuid.UUID
    jti: uuid.UUID
    email: str
    role: str
    permissions: list[str] = []
    iat: int
    exp: int

    @property
    def admin_id(self) -> uuid.UUID:
        """Читаемый псевдоним для `sub`.

        Returns:
            Идентификатор администратора.
        """
        return self.sub


CurrentAdmin = TokenPayload
"""Псевдоним для аннотаций эндпоинтов: `_admin: CurrentAdmin = Depends(...)`."""


class AuthError(HTTPException):
    """Ошибка аутентификации (401) в едином конверте ошибки проекта."""

    def __init__(self, message: str, code: str = "UNAUTHENTICATED") -> None:
        """Инициализирует исключение.

        Args:
            message: Человекочитаемая причина отказа.
            code: Машиночитаемый код ошибки.
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": code, "message": message, "details": None},
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedError(HTTPException):
    """Ошибка авторизации (403): токен валиден, но прав не хватает."""

    def __init__(self, missing: list[str]) -> None:
        """Инициализирует исключение.

        Args:
            missing: Права, которых не оказалось в claim `permissions`.
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Недостаточно прав для выполнения операции",
                "details": {"missing_permissions": missing},
            },
        )


@lru_cache(maxsize=1)
def get_public_key() -> str:
    """Декодирует публичный ключ RS256 из base64 в PEM.

    Ключ кешируется: парсить его на каждом запросе незачем, за время жизни
    процесса он не меняется. В окружении хранится в base64, потому что PEM
    содержит переносы строк и плохо переживает .env-файлы.

    Returns:
        Публичный ключ в формате PEM.

    Raises:
        ValueError: Ключ не задан или не декодируется в PEM.
    """
    raw = get_settings().jwt_public_key_b64
    if not raw:
        raise ValueError("JWT_PUBLIC_KEY_B64 не задан: проверка токенов невозможна")
    try:
        pem = base64.b64decode(raw).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("JWT_PUBLIC_KEY_B64 не является base64 от PEM") from exc
    if "BEGIN PUBLIC KEY" not in pem:
        raise ValueError(
            "JWT_PUBLIC_KEY_B64 декодируется не в PEM с публичным ключом "
            "(возможно, туда попал приватный ключ)"
        )
    return pem


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> TokenPayload:
    """Извлекает и проверяет access-токен из заголовка `Authorization`.

    Проверяются подпись, `exp`, `iss` и `aud` с допуском на расхождение часов.

    Args:
        credentials: Разобранный заголовок `Authorization: Bearer <token>`.
        settings: Настройки сервиса.

    Returns:
        Провалидированную полезную нагрузку токена.

    Raises:
        AuthError: Заголовка нет, токен просрочен, повреждён, подписан чужим
            ключом или не содержит обязательных claims.
    """
    if credentials is None or not credentials.credentials:
        raise AuthError("Требуется заголовок Authorization: Bearer <token>")

    try:
        claims = jwt.decode(
            credentials.credentials,
            key=get_public_key(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            leeway=settings.jwt_leeway_seconds,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Срок действия токена истёк", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        # Сюда попадают чужой iss/aud, неверная подпись и битый токен.
        # Наружу причину не раскрываем, в лог пишем.
        logger.warning("Отклонён токен: %s", exc)
        raise AuthError("Невалидный токен", code="INVALID_TOKEN") from exc

    try:
        return TokenPayload.model_validate(claims)
    except ValidationError as exc:
        logger.warning("Токен с валидной подписью, но неожиданными claims: %s", exc)
        raise AuthError("Невалидный токен", code="INVALID_TOKEN") from exc


def require_permission(
    *required: Permission,
) -> Callable[..., Awaitable[TokenPayload]]:
    """Создаёт зависимость FastAPI, требующую перечисленные права.

    Требуются ВСЕ перечисленные права одновременно. Зависимость можно вешать
    как на эндпоинт, так и на роутер целиком через `dependencies=[...]`.

    Args:
        *required: Права, необходимые для доступа к эндпоинту.

    Returns:
        Асинхронную зависимость, возвращающую полезную нагрузку токена.

    Example:
        >>> _admin: CurrentAdmin = Depends(
        ...     require_permission(Permission.MANAGE_PRODUCTS)
        ... )
    """
    required_values = [permission.value for permission in required]

    async def dependency(
        admin: TokenPayload = Depends(get_current_admin),
    ) -> TokenPayload:
        """Проверяет наличие требуемых прав в токене.

        Args:
            admin: Полезная нагрузка уже проверенного токена.

        Returns:
            Ту же полезную нагрузку, если прав достаточно.

        Raises:
            PermissionDeniedError: Не хватает хотя бы одного права.
        """
        granted = set(admin.permissions)
        missing = [value for value in required_values if value not in granted]
        if missing:
            logger.info(
                "Отказ в доступе админу %s (роль %s): не хватает прав %s",
                admin.admin_id,
                admin.role,
                missing,
            )
            raise PermissionDeniedError(missing)
        return admin

    return dependency


async def verify_service_token(
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    """Проверяет заголовок `X-Internal-Token` на internal-эндпоинтах.

    JWT здесь неприменим: orders_service не пользователь и токена админа не
    имеет. Сравнение через `secrets.compare_digest` — постоянное по времени,
    чтобы по времени ответа нельзя было подбирать ключ посимвольно.

    Args:
        x_internal_token: Значение заголовка из запроса.
        settings: Настройки сервиса.

    Raises:
        AuthError: Заголовок отсутствует или не совпадает с INTERNAL_API_KEY.
    """
    if x_internal_token is None or not secrets.compare_digest(
        x_internal_token, settings.internal_api_key
    ):
        logger.warning("Запрос к internal-эндпоинту с неверным X-Internal-Token")
        raise AuthError(
            "Неверный или отсутствующий X-Internal-Token",
            code="INVALID_SERVICE_TOKEN",
        )