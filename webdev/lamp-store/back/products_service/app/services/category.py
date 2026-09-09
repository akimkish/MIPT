"""Бизнес-логика управления категориями товаров."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.exceptions import ConflictError, NotFoundError


class CategoryService:
    """Сценарии работы с категориями каталога."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session
        self._repository = CategoryRepository(session)

    async def get(self, category_id: uuid.UUID) -> Category:
        """Возвращает категорию по идентификатору.

        Args:
            category_id: Идентификатор категории.

        Returns:
            Найденную категорию.

        Raises:
            NotFoundError: Если категория не найдена.
        """
        category = await self._repository.get_by_id(category_id)
        if category is None:
            raise NotFoundError(f"Категория {category_id} не найдена")
        return category

    async def list_categories(
        self, *, only_active: bool = True, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Category], int]:
        """Возвращает страницу категорий.

        Args:
            only_active: Возвращать только активные категории.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка категорий и их общего количества.
        """
        return await self._repository.list_all(
            only_active=only_active, limit=limit, offset=offset
        )

    async def create(self, data: CategoryCreate) -> Category:
        """Создаёт категорию.

        Args:
            data: Данные новой категории.

        Returns:
            Созданную категорию.

        Raises:
            ConflictError: Если категория с таким названием уже есть
                (сравнение без учёта регистра).
        """
        if await self._repository.get_by_name(data.name) is not None:
            raise ConflictError(f"Категория «{data.name}» уже существует")

        category = Category(**data.model_dump())
        await self._repository.create(category)
        await self._session.commit()
        return category

    async def update(self, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
        """Обновляет категорию.

        Args:
            category_id: Идентификатор категории.
            data: Изменяемые поля.

        Returns:
            Обновлённую категорию.

        Raises:
            NotFoundError: Если категория не найдена.
            ConflictError: Если новое название занято другой категорией.
        """
        category = await self.get(category_id)
        values = data.model_dump(exclude_unset=True)

        new_name = values.get("name")
        if new_name is not None:
            existing = await self._repository.get_by_name(new_name)
            if existing is not None and existing.category_id != category_id:
                raise ConflictError(f"Категория «{new_name}» уже существует")

        await self._repository.update(category, values)
        await self._session.commit()
        return category

    async def deactivate(self, category_id: uuid.UUID) -> Category:
        """Скрывает категорию с витрины.

        Физическое удаление категорий запрещено доменными правилами:
        на них ссылаются товары через `ON DELETE RESTRICT`, а старые
        записи должны оставаться читаемыми.

        Args:
            category_id: Идентификатор категории.

        Returns:
            Деактивированную категорию.

        Raises:
            NotFoundError: Если категория не найдена.
        """
        category = await self.get(category_id)
        await self._repository.update(category, {"is_active": False})
        await self._session.commit()
        return category
