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

    Args:
        credentials: Bearer-токен из заголовка `Authorization`.
        auth_service: Сервис аутентификации.

    Returns:
        Администратор, на которого выписан токен.
    """
    return await auth_service.get_current_admin(credentials.credentials)


def require_role(*allowed_roles: RoleName) -> Callable[[Admin], Admin]:
    """Строит зависимость, пускающую только администраторов с одной из ролей.

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
        """
        if RoleName(admin.role_name) not in allowed_roles:
            allowed = [role.value for role in allowed_roles]
            raise PermissionDeniedError(f"Требуется одна из ролей: {allowed}")
        return admin

    return dependency
