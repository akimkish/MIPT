import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName
from app.repositories.audit_log import AuditLogRepository
from tests.factories import auth_headers, create_admin


@pytest.mark.asyncio
class TestAuditLogCoverage:
    @pytest.mark.parametrize(
        ("action", "trigger"),
        [
            (AuditAction.LOGIN_SUCCESS, "login_success"),
            (AuditAction.LOGIN_FAILED, "login_failed"),
            (AuditAction.ADMIN_CREATED, "admin_created"),
            (AuditAction.ADMIN_DEACTIVATED, "admin_deactivated"),
            (AuditAction.ROLE_CHANGED, "role_changed"),
        ],
    )
    async def test_each_action_writes_exactly_one_entry(
        self, client, db_session, action, trigger
    ) -> None:
        """Каждое из пяти действий создаёт ровно одну запись audit_log."""
        actor, actor_password = await create_admin(
            db_session, role_name=RoleName.SUPERADMIN
        )

        if trigger == "login_success":
            await client.post(
                "/api/v1/auth/login",
                json={"email": actor.email, "password": actor_password},
            )
        elif trigger == "login_failed":
            await client.post(
                "/api/v1/auth/login", json={"email": actor.email, "password": "x"}
            )
        elif trigger == "admin_created":
            await client.post(
                "/api/v1/admins",
                json={
                    "email": "audit.created@lampstore.dev",
                    "full_name": "Audit Created",
                    "password": "correct-horse-battery-staple",
                    "role_name": RoleName.MODERATOR.value,
                },
                headers=auth_headers(actor),
            )
        elif trigger == "admin_deactivated":
            target, _ = await create_admin(db_session)
            await client.delete(
                f"/api/v1/admins/{target.admin_id}", headers=auth_headers(actor)
            )
        elif trigger == "role_changed":
            target, _ = await create_admin(db_session, role_name=RoleName.MODERATOR)
            await client.post(
                f"/api/v1/admins/{target.admin_id}/role",
                json={"new_role": RoleName.MANAGER.value},
                headers=auth_headers(actor),
            )

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == action.value)
        )
        assert len(result.scalars().all()) == 1

    async def test_list_for_admin_is_chronological_and_scoped(self, db_session) -> None:
        """list_for_admin возвращает записи по хронологии только для указанного admin_id."""
        admin_one, _ = await create_admin(db_session)
        admin_two, _ = await create_admin(db_session)
        repo = AuditLogRepository(db_session)

        await repo.record(
            action=AuditAction.LOGIN_SUCCESS,
            actor_email=admin_one.email,
            admin_id=admin_one.admin_id,
        )
        await repo.record(
            action=AuditAction.LOGIN_FAILED,
            actor_email=admin_two.email,
            admin_id=admin_two.admin_id,
        )
        await repo.record(
            action=AuditAction.LOGIN_SUCCESS,
            actor_email=admin_one.email,
            admin_id=admin_one.admin_id,
        )

        entries = await repo.list_for_admin(admin_one.admin_id)

        assert [e.admin_id for e in entries] == [admin_one.admin_id, admin_one.admin_id]
        assert entries[0].created_at <= entries[1].created_at

    def test_repository_has_no_update_method(self) -> None:
        """Структурная проверка неизменяемости журнала: своего update-метода нет."""
        assert not hasattr(AuditLogRepository, "update_entry")
