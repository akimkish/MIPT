import uuid

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName
from tests.factories import DEFAULT_PASSWORD, auth_headers, create_admin

VALID_CREATE_PAYLOAD = {
    "email": "new.admin@lampstore.dev",
    "full_name": "New Admin",
    "password": DEFAULT_PASSWORD,
    "role_name": RoleName.MODERATOR.value,
}


@pytest.mark.asyncio
class TestAdminsHappyPath:
    async def test_superadmin_creates_admin(self, client, db_session) -> None:
        """Superadmin создаёт админа -> 201, пароль в ответе отсутствует, аудит есть."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)

        response = await client.post(
            "/api/v1/admins", json=VALID_CREATE_PAYLOAD, headers=auth_headers(actor)
        )

        assert response.status_code == 201
        body = response.json()
        assert "password" not in body and "password_hash" not in body
        assert body["role_name"] == RoleName.MODERATOR.value

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == AuditAction.ADMIN_CREATED.value)
        )
        assert result.scalars().first() is not None

    async def test_list_admins_paginated(self, client, db_session) -> None:
        """Список администраторов возвращает total без учёта limit/offset."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        for _ in range(3):
            await create_admin(db_session)

        response = await client.get(
            "/api/v1/admins?limit=2&offset=0", headers=auth_headers(actor)
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        assert body["total"] >= 4  # actor + 3 созданных

    async def test_get_admin_by_id(self, client, db_session) -> None:
        """Карточка администратора по id."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        target, _ = await create_admin(db_session)

        response = await client.get(
            f"/api/v1/admins/{target.admin_id}", headers=auth_headers(actor)
        )

        assert response.status_code == 200
        assert response.json()["email"] == target.email

    async def test_update_full_name(self, client, db_session) -> None:
        """PATCH меняет full_name, не трогая role_name/is_active."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        target, _ = await create_admin(db_session, role_name=RoleName.MANAGER)

        response = await client.patch(
            f"/api/v1/admins/{target.admin_id}",
            json={"full_name": "Updated Name"},
            headers=auth_headers(actor),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["full_name"] == "Updated Name"
        assert body["role_name"] == RoleName.MANAGER.value

    async def test_deactivate_admin(self, client, db_session) -> None:
        """Деактивация -> is_active=False, запись admin_deactivated в аудите."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        target, _ = await create_admin(db_session)

        response = await client.delete(
            f"/api/v1/admins/{target.admin_id}", headers=auth_headers(actor)
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.ADMIN_DEACTIVATED.value,
                AuditLog.entity_id == target.admin_id,
            )
        )
        assert result.scalars().first() is not None

    async def test_change_role(self, client, db_session) -> None:
        """Смена роли -> role_name обновлён, аудит с old_role/new_role."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        target, _ = await create_admin(db_session, role_name=RoleName.MODERATOR)

        response = await client.post(
            f"/api/v1/admins/{target.admin_id}/role",
            json={"new_role": RoleName.MANAGER.value},
            headers=auth_headers(actor),
        )

        assert response.status_code == 200
        assert response.json()["role_name"] == RoleName.MANAGER.value

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.action == AuditAction.ROLE_CHANGED.value)
        )
        entry = result.scalars().first()
        assert entry is not None
        assert entry.payload == {
            "old_role": RoleName.MODERATOR.value,
            "new_role": RoleName.MANAGER.value,
        }


@pytest.mark.asyncio
class TestAdminsBoundaries:
    async def test_pagination_last_page_boundary(self, client, db_session) -> None:
        """limit=1 на последней записи не теряет и не дублирует элементы."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        _, total_before = (
            await client.get(
                "/api/v1/admins?limit=1&offset=0", headers=auth_headers(actor)
            )
        ).json(), None

        list_response = await client.get(
            "/api/v1/admins?limit=100&offset=0", headers=auth_headers(actor)
        )
        total = list_response.json()["total"]

        last_page = await client.get(
            f"/api/v1/admins?limit=1&offset={total - 1}", headers=auth_headers(actor)
        )
        assert len(last_page.json()["items"]) == 1

        beyond_last = await client.get(
            f"/api/v1/admins?limit=1&offset={total}", headers=auth_headers(actor)
        )
        assert beyond_last.json()["items"] == []

    async def test_password_min_length_boundary(self, client, db_session) -> None:
        """Пароль ровно минимальной длины принимается, короче — 422."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)

        ok_payload = {
            **VALID_CREATE_PAYLOAD,
            "email": "min8@lampstore.dev",
            "password": "a" * 8,
        }
        too_short_payload = {
            **VALID_CREATE_PAYLOAD,
            "email": "short@lampstore.dev",
            "password": "a" * 7,
        }

        ok_response = await client.post(
            "/api/v1/admins", json=ok_payload, headers=auth_headers(actor)
        )
        short_response = await client.post(
            "/api/v1/admins", json=too_short_payload, headers=auth_headers(actor)
        )

        assert ok_response.status_code == 201
        assert short_response.status_code == 422

    async def test_full_name_max_length_boundary(self, client, db_session) -> None:
        """full_name ровно 255 символов принимается, 256 — 422."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)

        ok_payload = {
            **VALID_CREATE_PAYLOAD,
            "email": "name255@lampstore.dev",
            "full_name": "A" * 255,
        }
        too_long_payload = {
            **VALID_CREATE_PAYLOAD,
            "email": "name256@lampstore.dev",
            "full_name": "A" * 256,
        }

        ok_response = await client.post(
            "/api/v1/admins", json=ok_payload, headers=auth_headers(actor)
        )
        long_response = await client.post(
            "/api/v1/admins", json=too_long_payload, headers=auth_headers(actor)
        )

        assert ok_response.status_code == 201
        assert long_response.status_code == 422


@pytest.mark.asyncio
class TestAdminsEdgeCases:
    async def test_duplicate_email_conflict(self, client, db_session) -> None:
        """Email, уже занятый другим админом, -> 409."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        existing, _ = await create_admin(db_session, email="taken@lampstore.dev")

        response = await client.post(
            "/api/v1/admins",
            json={**VALID_CREATE_PAYLOAD, "email": "taken@lampstore.dev"},
            headers=auth_headers(actor),
        )

        assert response.status_code == 409

    async def test_duplicate_email_different_case_conflict(
        self, client, db_session
    ) -> None:
        """Email, отличающийся только регистром от существующего, -> 409."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        await create_admin(db_session, email="case@lampstore.dev")

        response = await client.post(
            "/api/v1/admins",
            json={**VALID_CREATE_PAYLOAD, "email": "CASE@LampStore.dev"},
            headers=auth_headers(actor),
        )

        assert response.status_code == 409

    @pytest.mark.parametrize("role", [RoleName.MANAGER, RoleName.MODERATOR])
    async def test_non_superadmin_forbidden(self, client, db_session, role) -> None:
        """manager/moderator получают 403 на любой /admins эндпоинт."""
        actor, _ = await create_admin(db_session, role_name=role)

        response = await client.get("/api/v1/admins", headers=auth_headers(actor))

        assert response.status_code == 403

    async def test_missing_token_unauthorized_before_role_check(self, client) -> None:
        """Без токена -> 401, раньше проверки роли."""
        response = await client.get("/api/v1/admins")
        assert response.status_code == 401

    async def test_change_role_unknown_admin_id(self, client, db_session) -> None:
        """Смена роли несуществующего id -> 404."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)

        response = await client.post(
            f"/api/v1/admins/{uuid.uuid4()}/role",
            json={"new_role": RoleName.MANAGER.value},
            headers=auth_headers(actor),
        )

        assert response.status_code == 404

    async def test_deactivate_unknown_admin_id(self, client, db_session) -> None:
        """Деактивация несуществующего id -> 404."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)

        response = await client.delete(
            f"/api/v1/admins/{uuid.uuid4()}", headers=auth_headers(actor)
        )

        assert response.status_code == 404

    async def test_patch_empty_body_is_noop(self, client, db_session) -> None:
        """PATCH с пустым телом -> 200, данные не изменились."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        target, _ = await create_admin(db_session, role_name=RoleName.MANAGER)

        response = await client.patch(
            f"/api/v1/admins/{target.admin_id}", json={}, headers=auth_headers(actor)
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == target.full_name
        assert response.json()["role_name"] == RoleName.MANAGER.value

    async def test_patch_ignores_role_and_is_active_fields(
        self, client, db_session
    ) -> None:
        """role_name/is_active в теле PATCH игнорируются схемой AdminUpdate."""
        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)
        target, _ = await create_admin(db_session, role_name=RoleName.MANAGER)

        response = await client.patch(
            f"/api/v1/admins/{target.admin_id}",
            json={"role_name": "superadmin", "is_active": False},
            headers=auth_headers(actor),
        )

        assert response.status_code == 200
        assert response.json()["role_name"] == RoleName.MANAGER.value
        assert response.json()["is_active"] is True

    async def test_self_deactivation_currently_allowed(
        self, client, db_session
    ) -> None:

        actor, _ = await create_admin(db_session, role_name=RoleName.SUPERADMIN)

        response = await client.delete(
            f"/api/v1/admins/{actor.admin_id}", headers=auth_headers(actor)
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False
