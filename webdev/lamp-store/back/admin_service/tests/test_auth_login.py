from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName
from app.services.auth import LOCKOUT_DURATION, MAX_FAILED_LOGIN_ATTEMPTS
from tests.factories import create_admin


@pytest.mark.asyncio
class TestLoginHappyPath:
    async def test_successful_login_returns_token(self, client, db_session) -> None:
        """Верные email/пароль → 200 с access_token и token_type=bearer."""
        admin, password = await create_admin(db_session)

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": password}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str) and body["access_token"]

    async def test_login_email_case_insensitive(self, client, db_session) -> None:
        """Email в другом регистре находит запись, сохранённую в нижнем."""
        admin, password = await create_admin(db_session, email="lower@lampstore.dev")

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "LOWER@LampStore.DEV", "password": password},
        )

        assert response.status_code == 200

    async def test_successful_login_resets_failed_attempts(
        self, client, db_session
    ) -> None:
        """Успешный вход сбрасывает счётчик неудачных попыток и last_login."""
        admin, password = await create_admin(db_session, failed_login_attempts=3)

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": password}
        )

        assert response.status_code == 200
        await db_session.refresh(admin)
        assert admin.failed_login_attempts == 0
        assert admin.last_login is not None

    async def test_successful_login_writes_audit_log(self, client, db_session) -> None:
        """Успешный вход пишет login_success с корректным admin_id."""
        admin, password = await create_admin(db_session)

        await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": password}
        )

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.admin_id == admin.admin_id)
        )
        entries = result.scalars().all()
        assert any(e.action == AuditAction.LOGIN_SUCCESS.value for e in entries)


@pytest.mark.asyncio
class TestLoginLockout:
    async def test_attempt_before_threshold_not_locked(
        self, client, db_session
    ) -> None:
        """MAX-1 неудачных попыток — учётка ещё не заблокирована."""
        admin, password = await create_admin(
            db_session, failed_login_attempts=MAX_FAILED_LOGIN_ATTEMPTS - 1
        )

        wrong = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": "wrong"}
        )
        assert wrong.status_code == 401

    async def test_threshold_attempt_locks_account(self, client, db_session) -> None:
        """Ровно N-я неудачная попытка блокирует учётку -> 423."""
        admin, password = await create_admin(
            db_session, failed_login_attempts=MAX_FAILED_LOGIN_ATTEMPTS - 1
        )

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": "wrong"}
        )

        assert response.status_code == 401  # сама неверная попытка -> 401
        await db_session.refresh(admin)
        assert admin.failed_login_attempts == MAX_FAILED_LOGIN_ATTEMPTS
        assert admin.locked_until is not None

    async def test_locked_account_rejects_correct_password(
        self, client, db_session
    ) -> None:
        """Заблокированная учётка отклоняет даже верный пароль -> 423."""
        admin, password = await create_admin(
            db_session,
            failed_login_attempts=MAX_FAILED_LOGIN_ATTEMPTS,
            locked_until=datetime.now(timezone.utc) + LOCKOUT_DURATION,
        )

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": password}
        )

        assert response.status_code == 423

    async def test_lock_expired_allows_login(self, client, db_session) -> None:
        """locked_until в прошлом больше не блокирует вход."""
        admin, password = await create_admin(
            db_session,
            failed_login_attempts=MAX_FAILED_LOGIN_ATTEMPTS,
            locked_until=datetime.now(timezone.utc) - timedelta(seconds=1),
        )

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": password}
        )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestLoginEdgeCases:
    async def test_unknown_email_returns_generic_401(self, client) -> None:
        """Несуществующий email -> 401 с тем же кодом, что и неверный пароль."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@lampstore.dev", "password": "whatever"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_FAILED"

    async def test_wrong_password_increments_counter_and_logs(
        self, client, db_session
    ) -> None:
        """Неверный пароль -> 401, +1 к счётчику, запись login_failed с admin_id."""
        admin, password = await create_admin(db_session)

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": "wrong"}
        )

        assert response.status_code == 401
        await db_session.refresh(admin)
        assert admin.failed_login_attempts == 1

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.admin_id == admin.admin_id)
        )
        assert any(
            e.action == AuditAction.LOGIN_FAILED.value for e in result.scalars().all()
        )

    async def test_unknown_email_logs_without_admin_id(
        self, client, db_session
    ) -> None:
        """Несуществующий email -> в audit_log admin_id=NULL, actor_email сохранён."""
        await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@lampstore.dev", "password": "whatever"},
        )

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.actor_email == "ghost@lampstore.dev")
        )
        entries = result.scalars().all()
        assert len(entries) == 1
        assert entries[0].admin_id is None
        assert entries[0].action == AuditAction.LOGIN_FAILED.value

    async def test_inactive_account_rejected_before_password_check(
        self, client, db_session
    ) -> None:
        """Деактивированная учётка с верным паролем -> 403, попытка не тратится."""
        admin, password = await create_admin(db_session, is_active=False)

        response = await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": password}
        )

        assert response.status_code == 403
        await db_session.refresh(admin)
        assert admin.failed_login_attempts == 0

    async def test_locked_account_does_not_recount_attempt(
        self, client, db_session
    ) -> None:
        """Заблокированная учётка не увеличивает счётчик повторно."""
        admin, password = await create_admin(
            db_session,
            failed_login_attempts=MAX_FAILED_LOGIN_ATTEMPTS,
            locked_until=datetime.now(timezone.utc) + LOCKOUT_DURATION,
        )

        await client.post(
            "/api/v1/auth/login", json={"email": admin.email, "password": "wrong"}
        )

        await db_session.refresh(admin)
        assert admin.failed_login_attempts == MAX_FAILED_LOGIN_ATTEMPTS
