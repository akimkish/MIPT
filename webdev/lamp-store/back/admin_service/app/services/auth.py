"""Бизнес-логика аутентификации администраторов."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.admin import Admin
from app.models.enums import AuditAction
from app.repositories.admin import AdminRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.auth import TokenResponse
from app.services.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InactiveAccountError,
    NotFoundError,
)

MAX_FAILED_LOGIN_ATTEMPTS = 5
"""Порог неудачных входов подряд, после которого учётная запись блокируется.

Значение не зафиксировано ни в PROMPT_CONTEXT.md, ни в
INTEGRATION_CONTRACT.md — там есть только требование «блокировка после
N неудачных входов» и тест на сам факт блокировки. Это самостоятельно
выбранное число для учебного проекта; поменять — правка константы.
"""

LOCKOUT_DURATION = timedelta(minutes=15)
"""Длительность блокировки после достижения порога. Как и порог попыток —
не задано в исходных документах, выбрано как разумное для учебного масштаба."""


class AuthService:
    """Сценарии входа и проверки текущего администратора."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session
        self._admins = AdminRepository(session)
        self._audit = AuditLogRepository(session)

    async def login(
        self, email: str, password: str, *, ip_address: str | None = None
    ) -> TokenResponse:
        """Проверяет учётные данные и выпускает access-токен.

        Args:
            email: Email из формы входа (нормализуется в нижний регистр
                перед поиском).
            password: Пароль в открытом виде.
            ip_address: IP-адрес источника запроса для журнала аудита.

        Returns:
            Токен доступа для успешно вошедшего администратора.

        Raises:
            AuthenticationError: Если email не найден или пароль неверен.
                Сообщение одинаковое в обоих случаях — иначе перебором
                email можно узнать, какие адреса заведены в системе.
            AccountLockedError: Если учётная запись временно
                заблокирована после серии неудачных входов.
            InactiveAccountError: Если учётная запись деактивирована.
        """
        normalized_email = email.strip().lower()
        admin = await self._admins.get_by_email(normalized_email)

        if admin is None:
            await self._audit.record(
                action=AuditAction.LOGIN_FAILED,
                actor_email=normalized_email,
                ip_address=ip_address,
            )
            await self._session.commit()
            raise AuthenticationError("Неверный email или пароль")

        if admin.locked_until is not None and admin.locked_until > datetime.now(
            timezone.utc
        ):
            raise AccountLockedError(
                f"Учётная запись заблокирована до {admin.locked_until.isoformat()}"
            )

        if not admin.is_active:
            raise InactiveAccountError("Учётная запись деактивирована")

        if not verify_password(password, admin.password_hash):
            await self._register_failed_attempt(admin, ip_address)
            await self._session.commit()
            raise AuthenticationError("Неверный email или пароль")

        await self._admins.update(
            admin,
            {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": datetime.now(timezone.utc),
            },
        )
        await self._audit.record(
            action=AuditAction.LOGIN_SUCCESS,
            actor_email=admin.email,
            admin_id=admin.admin_id,
            ip_address=ip_address,
        )
        await self._session.commit()

        return TokenResponse(access_token=create_access_token(admin))

    async def _register_failed_attempt(
        self, admin: Admin, ip_address: str | None
    ) -> None:
        """Увеличивает счётчик неудачных входов и блокирует при превышении порога.

        Args:
            admin: Администратор, для которого не совпал пароль.
            ip_address: IP-адрес источника запроса для журнала аудита.
        """
        attempts = admin.failed_login_attempts + 1
        values: dict[str, object] = {"failed_login_attempts": attempts}
        if attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            values["locked_until"] = datetime.now(timezone.utc) + LOCKOUT_DURATION
        await self._admins.update(admin, values)
        await self._audit.record(
            action=AuditAction.LOGIN_FAILED,
            actor_email=admin.email,
            admin_id=admin.admin_id,
            ip_address=ip_address,
        )

    async def get_current_admin(self, token: str) -> Admin:
        """Возвращает администратора по access-токену (для `/auth/me`).

        Данные читаются из БД заново, а не берутся только из claims
        токена: `/auth/me` в пределах admin_service может себе это
        позволить (в отличие от products/orders, которые токен по БД не
        перепроверяют, см. INTEGRATION_CONTRACT.md → auth_contract) и
        отдаёт актуальные `full_name`/`role_name`, даже если они
        изменились после выпуска токена.

        Args:
            token: JWT из заголовка `Authorization: Bearer <token>`.

        Returns:
            Администратор, на которого выписан токен.

        Raises:
            AuthenticationError: Если токен невалиден или просрочен.
            NotFoundError: Если администратор из `sub` токена не найден
                (в норме такого быть не должно — админы не удаляются
                физически, — проверка защищает от рассинхрона данных,
                а не является ожидаемым штатным путём).
        """
        payload = decode_access_token(token)
        admin = await self._admins.get_by_id(payload.admin_id)
        if admin is None:
            raise NotFoundError("Администратор из токена не найден")
        return admin
