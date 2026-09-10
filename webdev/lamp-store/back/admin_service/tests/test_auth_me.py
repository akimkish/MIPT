from datetime import timedelta

import pytest

from app.models.enums import RoleName
from tests.factories import auth_headers, create_admin


@pytest.mark.asyncio
class TestMeHappyPath:
    async def test_returns_current_admin_profile(self, client, db_session) -> None:
        """Валидный токен -> 200, поля совпадают, password_hash отсутствует."""
        admin, _ = await create_admin(db_session, role_name=RoleName.MANAGER)

        response = await client.get("/api/v1/auth/me", headers=auth_headers(admin))

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == admin.email
        assert body["role_name"] == RoleName.MANAGER.value
        assert "password_hash" not in body

    async def test_reflects_changes_made_after_token_issue(
        self, client, db_session
    ) -> None:
        """/auth/me отдаёт актуальную роль, даже если её сменили после выпуска токена."""
        admin, _ = await create_admin(db_session, role_name=RoleName.MANAGER)
        headers = auth_headers(admin)  # токен выпущен со старой ролью

        admin.role_name = RoleName.SUPERADMIN.value
        await db_session.flush()
        await db_session.refresh(admin)  # синхронизирует серверные поля (updated_at)

        response = await client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["role_name"] == RoleName.SUPERADMIN.value


@pytest.mark.asyncio
class TestMeBoundaries:
    async def test_token_about_to_expire_accepted(
        self, client, db_session, make_token
    ) -> None:
        """Токен с exp через 1 секунду ещё валиден."""
        admin, _ = await create_admin(db_session)
        token = make_token(admin, exp_delta=timedelta(seconds=1))

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    async def test_just_expired_token_rejected(
        self, client, db_session, make_token
    ) -> None:

        admin, _ = await create_admin(db_session)
        token = make_token(admin, exp_delta=timedelta(seconds=-15))

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestMeEdgeCases:
    async def test_missing_authorization_header(self, client) -> None:
        """Без заголовка Authorization -> 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_expired_token(self, client, db_session, make_token) -> None:
        """Явно просроченный токен -> 401."""
        admin, _ = await create_admin(db_session)
        token = make_token(admin, exp_delta=timedelta(minutes=-31))

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    async def test_wrong_issuer(self, client, db_session, make_token) -> None:
        """Токен с чужим iss -> 401."""
        admin, _ = await create_admin(db_session)
        token = make_token(admin, issuer="not-admin-service")

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    async def test_wrong_audience(self, client, db_session, make_token) -> None:
        """Токен с чужим aud -> 401."""
        admin, _ = await create_admin(db_session)
        token = make_token(admin, audience="not-lamp-store")

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    async def test_token_for_nonexistent_admin(
        self, client, db_session, make_token
    ) -> None:
        """Валидная подпись, но sub указывает на несуществующего админа."""
        admin, _ = await create_admin(db_session)
        await db_session.delete(admin)
        await db_session.flush()
        token = make_token(admin)  # объект в Python ещё жив, admin_id известен

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in (401, 404)

    async def test_malformed_token(self, client) -> None:
        """Не-JWT строка -> 401, а не 500."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not-a-jwt"},
        )
        assert response.status_code == 401

    async def test_token_signed_with_wrong_key(
        self, client, db_session, make_token, wrong_rsa_keypair
    ) -> None:
        """Токен, подписанный чужим приватным ключом, -> 401."""
        wrong_private_key, _ = wrong_rsa_keypair
        admin, _ = await create_admin(db_session)
        token = make_token(admin, signing_key=wrong_private_key)

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
