import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.admin import Admin
from app.models.enums import AuditAction, RoleName
from app.repositories.admin import AdminRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.admin import AdminCreate, AdminUpdate
from app.services.exceptions import ConflictError, NotFoundError, PermissionDeniedError


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._admins = AdminRepository(session)
        self._audit = AuditLogRepository(session)

    async def get(self, admin_id: uuid.UUID) -> Admin:
        admin = await self._admins.get_by_id(admin_id)
        if admin is None:
            raise NotFoundError(f"Администратор {admin_id} не найден")
        return admin

    async def list_admins(
        self, *, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Admin], int]:

        return await self._admins.list(limit=limit, offset=offset)

    async def create(self, data: AdminCreate, *, actor: Admin) -> Admin:

        self._require_superadmin(actor)

        normalized_email = data.email.strip().lower()
        if await self._admins.get_by_email(normalized_email) is not None:
            raise ConflictError(f"Email «{normalized_email}» уже используется")

        admin = Admin(
            email=normalized_email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role_name=data.role_name.value,
        )
        await self._admins.create(admin)
        await self._audit.record(
            action=AuditAction.ADMIN_CREATED,
            actor_email=actor.email,
            admin_id=actor.admin_id,
            entity_type="admin",
            entity_id=admin.admin_id,
            payload={"role_name": admin.role_name},
        )
        await self._session.commit()
        return admin

    async def update(self, admin_id: uuid.UUID, data: AdminUpdate) -> Admin:

        admin = await self.get(admin_id)
        values = data.model_dump(exclude_unset=True, exclude={"is_active"})
        if not values:
            return admin
        await self._admins.update(admin, values)
        await self._session.commit()
        return admin

    async def deactivate(self, admin_id: uuid.UUID, *, actor: Admin) -> Admin:

        self._require_superadmin(actor)
        admin = await self.get(admin_id)

        await self._admins.update(admin, {"is_active": False})
        await self._audit.record(
            action=AuditAction.ADMIN_DEACTIVATED,
            actor_email=actor.email,
            admin_id=actor.admin_id,
            entity_type="admin",
            entity_id=admin.admin_id,
        )
        await self._session.commit()
        return admin

    async def change_role(
        self, admin_id: uuid.UUID, new_role: RoleName, *, actor: Admin
    ) -> Admin:

        self._require_superadmin(actor)
        admin = await self.get(admin_id)
        old_role = admin.role_name

        await self._admins.update(admin, {"role_name": new_role.value})
        await self._audit.record(
            action=AuditAction.ROLE_CHANGED,
            actor_email=actor.email,
            admin_id=actor.admin_id,
            entity_type="admin",
            entity_id=admin.admin_id,
            payload={"old_role": old_role, "new_role": new_role.value},
        )
        await self._session.commit()
        return admin

    async def bootstrap_first_admin(self, email: str, password: str) -> None:

        if await self._admins.exists_any():
            return

        admin = Admin(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            full_name="Superadmin",
            role_name=RoleName.SUPERADMIN.value,
        )
        try:
            await self._admins.create(admin)
            await self._session.commit()
        except IntegrityError:
            # Другая реплика сервиса успела создать первого админа раньше.
            await self._session.rollback()

    @staticmethod
    def _require_superadmin(actor: Admin) -> None:

        if actor.role_name != RoleName.SUPERADMIN.value:
            raise PermissionDeniedError("Действие доступно только superadmin")
