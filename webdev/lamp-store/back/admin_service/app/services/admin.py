"""Бизнес-логика управления администраторами (CRUD, доступный только superadmin)."""

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
    """Сценарии управления учётными записями администраторов.

    Каждый изменяющий метод принимает `actor` — администратора,
    выполняющего действие, — и сам проверяет `role_name == superadmin`.
    Это дублирует проверку, которую логично сделать и зависимостью
    FastAPI в `api/v1/admins.py`, но здесь она нужна, чтобы сервис был
    корректен независимо от вызывающего кода и тестировался без
    поднятия HTTP-слоя.

    Защита последнего активного superadmin от деактивации/смены роли
    НЕ реализована: в исходных документах такого требования нет, а
    добавлять его «на всякий случай» — лишняя сложность сверх задачи.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session
        self._admins = AdminRepository(session)
        self._audit = AuditLogRepository(session)

    async def get(self, admin_id: uuid.UUID) -> Admin:
        """Возвращает администратора по идентификатору.

        Args:
            admin_id: Идентификатор администратора.

        Returns:
            Найденный администратор.

        Raises:
            NotFoundError: Если администратор не найден.
        """
        admin = await self._admins.get_by_id(admin_id)
        if admin is None:
            raise NotFoundError(f"Администратор {admin_id} не найден")
        return admin

    async def list_admins(
        self, *, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Admin], int]:
        """Возвращает постраничный список администраторов.

        Args:
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка администраторов и их общего количества.
        """
        return await self._admins.list(limit=limit, offset=offset)

    async def create(self, data: AdminCreate, *, actor: Admin) -> Admin:
        """Создаёт нового администратора.

        Args:
            data: Данные новой учётной записи.
            actor: Администратор, выполняющий создание.

        Returns:
            Созданный администратор.

        Raises:
            PermissionDeniedError: Если `actor` не superadmin.
            ConflictError: Если email уже занят.
        """
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
        """Обновляет неаудируемые поля администратора (`full_name`).

        `is_active` и `role_name` сюда не входят — деактивация и смена
        роли вынесены в `deactivate`/`change_role`, потому что обе
        операции требуют записи в `audit_log`, а обычный PATCH — нет.

        Args:
            admin_id: Идентификатор администратора.
            data: Изменяемые поля.

        Returns:
            Обновлённый администратор.

        Raises:
            NotFoundError: Если администратор не найден.
        """
        admin = await self.get(admin_id)
        values = data.model_dump(exclude_unset=True, exclude={"is_active"})
        if not values:
            return admin
        await self._admins.update(admin, values)
        await self._session.commit()
        return admin

    async def deactivate(self, admin_id: uuid.UUID, *, actor: Admin) -> Admin:
        """Деактивирует учётную запись администратора.

        Физическое удаление запрещено доменом — только `is_active=False`.
        Уже выданный токен деактивированного администратора остаётся
        валиден до истечения TTL — осознанное упрощение реализации JWT
        (PROMPT_CONTEXT.md → known_limitations, п.3), не этого метода.

        Args:
            admin_id: Идентификатор администратора.
            actor: Администратор, выполняющий деактивацию.

        Returns:
            Деактивированный администратор.

        Raises:
            PermissionDeniedError: Если `actor` не superadmin.
            NotFoundError: Если администратор не найден.
        """
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
        """Меняет роль администратора и пишет событие в журнал аудита.

        Args:
            admin_id: Идентификатор администратора, чья роль меняется.
            new_role: Новая роль.
            actor: Администратор, выполняющий смену роли.

        Returns:
            Администратор с обновлённой ролью.

        Raises:
            PermissionDeniedError: Если `actor` не superadmin.
            NotFoundError: Если администратор не найден.
        """
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
        """Создаёт первого администратора при пустой таблице `admins`.

        Вызывается один раз при старте сервиса из `FIRST_ADMIN_EMAIL` /
        `FIRST_ADMIN_PASSWORD`. Проверка «таблица пуста» и вставка не
        объединены в одну атомарную операцию — между ними возможна гонка
        при параллельном старте нескольких реплик. Закрывается это не
        транзакционной блокировкой (избыточно для однократного действия
        при старте), а перехватом `IntegrityError` от UNIQUE по `email`.

        Args:
            email: Email первого администратора из переменных окружения.
            password: Пароль первого администратора в открытом виде.
        """
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
        """Проверяет, что действие выполняет superadmin.

        Args:
            actor: Администратор, инициировавший действие.

        Raises:
            PermissionDeniedError: Если роль `actor` не `superadmin`.
        """
        if actor.role_name != RoleName.SUPERADMIN.value:
            raise PermissionDeniedError("Действие доступно только superadmin")
