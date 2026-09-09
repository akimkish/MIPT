"""Обобщённый репозиторий с базовыми CRUD-операциями."""

import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Базовый репозиторий для моделей с UUID-первичным ключом.

    Инкапсулирует однотипный доступ к БД: получение по id, постраничный
    список с фильтрами точного совпадения, создание, обновление набора
    полей, физическое удаление. Специфичные для сущности выборки (поиск
    по email, JOIN с другими таблицами и т.п.) описываются в наследнике
    отдельным методом — базовый класс намеренно их не содержит, чтобы не
    превращаться в свалку метода на каждый случай использования (см.
    пример `ProductRepository._catalog_conditions` в products_service —
    там сложная фильтрация тоже осталась в конкретном репозитории).

    Физическое удаление (`delete`) в проекте разрешено не для всех
    сущностей (PROMPT_CONTEXT.md → domain_decisions → «Удаление»): для
    `admins` наследник его просто не вызывает, используя вместо этого
    `update(..., {"is_active": False})`.
    """

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
            model: ORM-класс, с которым работает репозиторий.
        """
        self._session = session
        self.model = model

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        """Возвращает запись по первичному ключу.

        Args:
            entity_id: Значение первичного ключа.

        Returns:
            Найденная запись или `None`.
        """
        return await self._session.get(self.model, entity_id)

    async def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        order_by: Any = None,
        **filters: Any,
    ) -> tuple[Sequence[ModelT], int]:
        """Возвращает постраничный список записей и их общее количество.

        Фильтры передаются как `поле=значение` и трактуются как точное
        совпадение (`WHERE model.поле == значение`) — этого достаточно
        для учебного масштаба (например, `role_name=...`,
        `is_active=True`). Диапазоны, поиск по подстроке и JOIN остаются
        в репозиториях конкретных сущностей.

        Args:
            limit: Размер страницы.
            offset: Смещение от начала выборки.
            order_by: Колонка или выражение сортировки; по умолчанию не
                задаётся.
            **filters: Пары «имя поля модели → значение» для точного
                сравнения.

        Returns:
            Кортеж из списка записей текущей страницы и общего
            количества записей, подходящих под фильтры (без `limit`/
            `offset`).

        Raises:
            AttributeError: Если среди `filters` указано имя, которого
                нет в модели.
        """
        conditions = [
            getattr(self.model, field) == value for field, value in filters.items()
        ]

        items_stmt = select(self.model).where(*conditions).limit(limit).offset(offset)
        if order_by is not None:
            items_stmt = items_stmt.order_by(order_by)

        total_stmt = select(func.count()).select_from(self.model).where(*conditions)

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def create(self, entity: ModelT) -> ModelT:
        """Добавляет запись в сессию и получает значения, заполненные БД.

        Args:
            entity: Заполненный ORM-объект.

        Returns:
            Тот же объект со значениями по умолчанию/сервером (например,
            временными метками).
        """
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelT, values: dict[str, Any]) -> ModelT:
        """Применяет набор изменённых полей к записи.

        Args:
            entity: Существующий ORM-объект.
            values: Словарь «поле → новое значение».

        Returns:
            Обновлённый ORM-объект.
        """
        for field, value in values.items():
            setattr(entity, field, value)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Физически удаляет запись.

        Не вызывается для сущностей, где домен запрещает физическое
        удаление (`admins`, `products`, `promos`) — для них есть только
        `update(..., {"is_active": False})`. Оставлен в базовом классе
        для сущностей, где удаление разрешено (например, `reviews`).

        Args:
            entity: Существующий ORM-объект для удаления.
        """
        await self._session.delete(entity)
        await self._session.flush()