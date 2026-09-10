import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        """Возвращает категорию по идентификатору.

        Args:
            category_id: Идентификатор категории.

        Returns:
            Категорию или `None`, если она не найдена.
        """
        return await self._session.get(Category, category_id)

    async def get_by_name(self, name: str) -> Category | None:
        """Возвращает категорию по названию без учёта регистра.

        Args:
            name: Название категории в любом регистре.

        Returns:
            Категорию или None, если она не найдена.
        """
        stmt = select(Category).where(func.lower(Category.name) == name.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, *, only_active: bool = True, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Category], int]:
        """Возвращает страницу категорий и общее их количество.

        Args:
            only_active: Возвращать только категории с `is_active=True`.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка категорий текущей страницы и общего
            количества подходящих записей (без учёта пагинации).
        """
        conditions = [Category.is_active.is_(True)] if only_active else []

        items_stmt = (
            select(Category)
            .where(*conditions)
            .order_by(Category.name)
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(Category).where(*conditions)

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def create(self, category: Category) -> Category:
        """Добавляет категорию в сессию и получает её сгенерированные поля.

        Args:
            category: Заполненный ORM-объект категории.

        Returns:
            Тот же объект с заполненными `created_at` / `updated_at`.
        """
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def update(self, category: Category, values: dict[str, object]) -> Category:
        """Применяет к категории набор изменённых полей.

        Args:
            category: Существующий ORM-объект категории.
            values: Словарь «поле → новое значение» (обычно результат
                `schema.model_dump(exclude_unset=True)`).

        Returns:
            Обновлённый ORM-объект категории.
        """
        for field, value in values.items():
            setattr(category, field, value)
        await self._session.flush()
        await self._session.refresh(category)
        return category
