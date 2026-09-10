import asyncio

import pytest
from sqlalchemy import select

from app.models.admin import Admin
from app.models.enums import RoleName
from app.services.admin import AdminService


@pytest.mark.asyncio
class TestBootstrapFirstAdmin:
    async def test_creates_admin_on_empty_table(self, db_session) -> None:
        """Пустая таблица -> создаётся superadmin с переданными данными."""
        service = AdminService(db_session)

        await service.bootstrap_first_admin("root@lampstore.dev", "bootstrap-pass")

        result = await db_session.execute(select(Admin))
        admins = result.scalars().all()
        assert len(admins) == 1
        assert admins[0].email == "root@lampstore.dev"
        assert admins[0].role_name == RoleName.SUPERADMIN.value
        assert admins[0].password_hash != "bootstrap-pass"

    async def test_noop_on_nonempty_table(self, db_session) -> None:
        """Непустая таблица -> вызов ничего не создаёт."""
        service = AdminService(db_session)
        await service.bootstrap_first_admin("first@lampstore.dev", "pass-one")

        await service.bootstrap_first_admin("second@lampstore.dev", "pass-two")

        result = await db_session.execute(select(Admin))
        admins = result.scalars().all()
        assert len(admins) == 1
        assert admins[0].email == "first@lampstore.dev"

    async def test_concurrent_bootstrap_creates_exactly_one_admin(
        self, test_engine
    ) -> None:
        """Гонка: два параллельных bootstrap на пустой таблице -> ровно одна запись."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

        async def _bootstrap() -> None:
            async with session_factory() as session:
                await AdminService(session).bootstrap_first_admin(
                    "race@lampstore.dev", "race-pass"
                )

        await asyncio.gather(_bootstrap(), _bootstrap())

        async with session_factory() as session:
            result = await session.execute(select(Admin))
            admins = result.scalars().all()

        assert len(admins) == 1

        async with session_factory() as session:
            await session.execute(Admin.__table__.delete())
            await session.commit()
