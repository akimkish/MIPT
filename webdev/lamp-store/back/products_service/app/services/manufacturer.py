"""Бизнес-логика управления производителями."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturer import Manufacturer
from app.repositories.manufacturer import ManufacturerRepository
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate
from app.services.exceptions import ConflictError, NotFoundError


class ManufacturerService:
    """Сценарии работы с производителями каталога."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session
        self._repository = ManufacturerRepository(session)

    async def get(self, manufacturer_id: uuid.UUID) -> Manufacturer:
        """Возвращает производителя по идентификатору.

        Args:
            manufacturer_id: Идентификатор производителя.

        Returns:
            Найденного производителя.

        Raises:
            NotFoundError: Если производитель не найден.
        """
        manufacturer = await self._repository.get_by_id(manufacturer_id)
        if manufacturer is None:
            raise NotFoundError(f"Производитель {manufacturer_id} не найден")
        return manufacturer

    async def list_manufacturers(
        self, *, only_active: bool = True, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Manufacturer], int]:
        """Возвращает страницу производителей.

        Args:
            only_active: Возвращать только активные записи.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка производителей и их общего количества.
        """
        return await self._repository.list_all(
            only_active=only_active, limit=limit, offset=offset
        )

    async def create(self, data: ManufacturerCreate) -> Manufacturer:
        """Создаёт производителя.

        Args:
            data: Данные нового производителя.

        Returns:
            Созданного производителя.

        Raises:
            ConflictError: Если производитель с таким названием уже есть.
        """
        if await self._repository.get_by_name(data.name) is not None:
            raise ConflictError(f"Производитель «{data.name}» уже существует")

        manufacturer = Manufacturer(**data.model_dump())
        await self._repository.create(manufacturer)
        await self._session.commit()
        return manufacturer

    async def update(
        self, manufacturer_id: uuid.UUID, data: ManufacturerUpdate
    ) -> Manufacturer:
        """Обновляет производителя.

        Args:
            manufacturer_id: Идентификатор производителя.
            data: Изменяемые поля.

        Returns:
            Обновлённого производителя.

        Raises:
            NotFoundError: Если производитель не найден.
            ConflictError: Если новое название занято другой записью.
        """
        manufacturer = await self.get(manufacturer_id)
        values = data.model_dump(exclude_unset=True)

        new_name = values.get("name")
        if new_name is not None:
            existing = await self._repository.get_by_name(new_name)
            if existing is not None and existing.manufacturer_id != manufacturer_id:
                raise ConflictError(f"Производитель «{new_name}» уже существует")

        await self._repository.update(manufacturer, values)
        await self._session.commit()
        return manufacturer

    async def deactivate(self, manufacturer_id: uuid.UUID) -> Manufacturer:
        """Скрывает производителя с витрины.

        Args:
            manufacturer_id: Идентификатор производителя.

        Returns:
            Деактивированного производителя.

        Raises:
            NotFoundError: Если производитель не найден.
        """
        manufacturer = await self.get(manufacturer_id)
        await self._repository.update(manufacturer, {"is_active": False})
        await self._session.commit()
        return manufacturer
