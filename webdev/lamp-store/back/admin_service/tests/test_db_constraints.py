import uuid

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from app.models.admin import Admin
from app.models.audit_log import AuditLog
from tests.factories import build_admin


@pytest.mark.asyncio
class TestAdminConstraints:
    async def test_invalid_role_name_rejected_by_check(self, db_session) -> None:
        """INSERT с role_name вне допустимого списка отбивается CHECK на уровне БД."""
        admin = build_admin()
        stmt = insert(Admin.__table__).values(
            admin_id=uuid.uuid4(),
            email=admin.email,
            password_hash=admin.password_hash,
            full_name=admin.full_name,
            role_name="wat",  # значение вне ('superadmin','manager','moderator')
        )

        with pytest.raises(IntegrityError):
            await db_session.execute(stmt)
            await db_session.flush()

    async def test_negative_failed_login_attempts_rejected(self, db_session) -> None:
        """Отрицательное значение failed_login_attempts отбивается CHECK."""
        admin = build_admin()
        stmt = insert(Admin.__table__).values(
            admin_id=uuid.uuid4(),
            email=admin.email,
            password_hash=admin.password_hash,
            full_name=admin.full_name,
            role_name="manager",
            failed_login_attempts=-1,
        )

        with pytest.raises(IntegrityError):
            await db_session.execute(stmt)
            await db_session.flush()

    async def test_duplicate_email_rejected_at_db_level(self, db_session) -> None:
        """Дубликат email отбивается UNIQUE-ограничением, даже мимо сервисного слоя."""
        first = build_admin(email="dup@lampstore.dev")
        db_session.add(first)
        await db_session.flush()

        second = build_admin(email="dup@lampstore.dev")
        db_session.add(second)

        with pytest.raises(IntegrityError):
            await db_session.flush()


@pytest.mark.asyncio
class TestAuditLogConstraints:
    async def test_invalid_action_rejected_by_check(self, db_session) -> None:
        """INSERT с action вне допустимого списка отбивается CHECK на уровне БД."""
        stmt = insert(AuditLog.__table__).values(
            log_id=uuid.uuid4(),
            actor_email="someone@lampstore.dev",
            action="not_a_real_action",
        )

        with pytest.raises(IntegrityError):
            await db_session.execute(stmt)
            await db_session.flush()

    async def test_reference_to_missing_admin_rejected_by_fk(self, db_session) -> None:
        """Ссылка на несуществующий admin_id отбивается внешним ключом."""
        stmt = insert(AuditLog.__table__).values(
            log_id=uuid.uuid4(),
            admin_id=uuid.uuid4(),  # заведомо не существует
            actor_email="someone@lampstore.dev",
            action="login_success",
        )

        with pytest.raises(IntegrityError):
            await db_session.execute(stmt)
            await db_session.flush()