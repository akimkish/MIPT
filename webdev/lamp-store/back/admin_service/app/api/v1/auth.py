from fastapi import APIRouter, Depends, Request

from app.api.deps import get_auth_service, get_current_admin
from app.models.admin import Admin
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход администратора",
    description=(
        "Проверяет email и пароль, выпускает access-токен (RS256, TTL "
        "30 минут). После серии неудачных попыток входа учётная запись "
        "временно блокируется. Refresh-токена нет: после истечения TTL "
        "нужен повторный вход."
    ),
    responses={
        401: {"description": "Неверный email или пароль"},
        403: {"description": "Учётная запись деактивирована"},
        423: {"description": "Учётная запись временно заблокирована"},
    },
)
async def login(
    data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Аутентифицирует администратора и выпускает access-токен.

    Args:
        data: Email и пароль из формы входа.
        request: Текущий запрос — используется только для получения
            IP-адреса источника для журнала аудита.
        auth_service: Сервис аутентификации.

    Returns:
        Access-токен и тип токена (`bearer`).

    """
    return await auth_service.login(
        data.email,
        data.password,
        ip_address=request.client.host if request.client else None,
    )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Данные текущего администратора",
    description=(
        "Возвращает профиль администратора, выписавшего переданный " "access-токен."
    ),
    responses={401: {"description": "Токен невалиден, просрочен или админ не найден"}},
)
async def get_me(admin: Admin = Depends(get_current_admin)) -> MeResponse:
    """Возвращает профиль текущего администратора.

    Args:
        admin: Администратор, аутентифицированный по токену.

    Returns:
        Профиль администратора без `password_hash`.
    """
    return MeResponse.model_validate(admin)
