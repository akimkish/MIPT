"""Зависимости FastAPI: сессия БД, аутентификация, доступ по ролям."""

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.models.admin import Admin
from app.models.enums import RoleName
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.exceptions import PermissionDeniedError

_bearer_scheme = HTTPBearer(
    auto_error=True, description="Access-токен, выданный POST /auth/login"
)


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Собирает `AuthService` с сессией текущего запроса.

    Args:
        session: Асинхронная сессия SQLAlchemy текущего запроса.

    Returns:
        Готовый к использованию сервис аутентификации.
    """
    return AuthService(session)


def get_admin_service(session: AsyncSession = Depends(get_session)) -> AdminService:
    """Собирает `AdminService` с сессией текущего запроса.

    Args:
        session: Асинхронная сессия SQLAlchemy текущего запроса.

    Returns:
        Готовый к использованию сервис управления администраторами.
    """
    return AdminService(session)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> Admin:
    """Возвращает администратора, аутентифицированного по access-токену.

    В отличие от products_service/orders_service, где токен проверяется
    только по подписи и claims (`role`/`permissions` доверяются как
    есть), admin_service — источник истины по администраторам и может
    позволить себе поход в БД на каждый запрос: `AuthService` перечитывает
    `role_name`/`is_active` из таблицы, а не доверяет содержимому токена.

    Args:
        credentials: Bearer-токен из заголовка `Authorization`.
        auth_service: Сервис аутентификации.

    Returns:
        Администратор, на которого выписан токен.

    Raises:
        AuthenticationError: Если токен невалиден, просрочен, либо
            администратор из `sub` не найден (HTTP 401).
    """
    return await auth_service.get_current_admin(credentials.credentials)


def require_role(*allowed_roles: RoleName) -> Callable[[Admin], Admin]:
    """Строит зависимость, пускающую только администраторов с одной из ролей.

    Фабрика, а не сама зависимость: `require_role(RoleName.SUPERADMIN)`
    вызывается один раз при объявлении роутера и возвращает функцию для
    `Depends(...)`. Для трёх фиксированных ролей и единственной
    проверяемой в этом сервисе операции (управление админами) такой
    подход проще отдельной модели `Permission`, как в products/orders,
    где прав много и они комбинируются — заводить её здесь ради одной
    проверки было бы лишней абстракцией.

    Args:
        *allowed_roles: Роли, которым разрешён доступ к эндпоинту.

    Returns:
        Функция-зависимость FastAPI, возвращающая текущего
        администратора при успешной проверке роли.
    """

    def dependency(admin: Admin = Depends(get_current_admin)) -> Admin:
        """Проверяет роль текущего администратора.

        Args:
            admin: Администратор, аутентифицированный по токену.

        Returns:
            Тот же администратор, если его роль допущена.

        Raises:
            PermissionDeniedError: Если роль администратора не входит
                в `allowed_roles` (HTTP 403).
        """
        if RoleName(admin.role_name) not in allowed_roles:
            allowed = [role.value for role in allowed_roles]
            raise PermissionDeniedError(f"Требуется одна из ролей: {allowed}")
        return admin

    return dependency