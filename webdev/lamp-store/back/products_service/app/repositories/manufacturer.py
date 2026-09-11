import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturer import Manufacturer


class ManufacturerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, manufacturer_id: uuid.UUID) -> Manufacturer | None:
        """Возвращает производителя по идентификатору.

        Args:
            manufacturer_id: Идентификатор производителя.

        Returns:
            Производителя или `None`, если он не найден.
        """
        return await self._session.get(Manufacturer, manufacturer_id)

    async def get_by_name(self, name: str) -> Manufacturer | None:
        """Возвращает производителя по названию без учёта регистра.

        Args:
            name: Название производителя в любом регистре.

        Returns:
            Производителя или `None`, если он не найден.
        """
        stmt = select(Manufacturer).where(func.lower(Manufacturer.name) == name.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, *, only_active: bool = True, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Manufacturer], int]:
        """Возвращает страницу производителей и общее их количество.

        Args:
            only_active: Возвращать только записи с `is_active=True`.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка производителей и общего количества записей.
        """
        conditions = [Manufacturer.is_active.is_(True)] if only_active else []

        items_stmt = (
            select(Manufacturer)
            .where(*conditions)
            .order_by(Manufacturer.name)
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(Manufacturer).where(*conditions)

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def create(self, manufacturer: Manufacturer) -> Manufacturer:
        """Добавляет производителя в сессию.

        Args:
            manufacturer: Заполненный ORM-объект производителя.

        Returns:
            Тот же объект с заполненными временными метками.
        """
        self._session.add(manufacturer)
        await self._session.flush()
        await self._session.refresh(manufacturer)
        return manufacturer

    async def update(
        self, manufacturer: Manufacturer, values: dict[str, object]
    ) -> Manufacturer:
        """Применяет к производителю набор изменённых полей.

        Args:
            manufacturer: Существующий ORM-объект производителя.
            values: Словарь «поле → новое значение».

        Returns:
            Обновлённый ORM-объект производителя.
        """
        for field, value in values.items():
            setattr(manufacturer, field, value)
        await self._session.flush()
        await self._session.refresh(manufacturer)
        return manufacturer
