"""Репозиторий доступа к таблице отзывов."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    """Доступ к данным отзывов на товары.

    Единственная сущность сервиса, для которой разрешено физическое
    удаление (модерация), и единственная без метода обновления
    содержимого: отзыв неизменяем, меняется только флаг `is_approved`.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Открытая асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        """Возвращает отзыв по идентификатору.

        Args:
            review_id: Идентификатор отзыва.

        Returns:
            Отзыв или `None`, если он не найден.
        """
        return await self._session.get(Review, review_id)

    async def get_by_product_and_email(
        self, product_id: uuid.UUID, user_email: str
    ) -> Review | None:
        """Ищет отзыв конкретного автора на конкретный товар.

        Нужен для дружелюбной проверки повторного отзыва до вставки —
        иначе пользователь получит ошибку UNIQUE-ограничения.

        Args:
            product_id: Идентификатор товара.
            user_email: Email автора (ожидается уже нормализованным
                в нижний регистр Pydantic-схемой).

        Returns:
            Отзыв или `None`, если его нет.
        """
        stmt = select(Review).where(
            Review.product_id == product_id,
            Review.user_email == user_email,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_product(
        self,
        product_id: uuid.UUID,
        *,
        only_approved: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Review], int]:
        """Возвращает страницу отзывов на товар и их общее количество.

        Args:
            product_id: Идентификатор товара.
            only_approved: Возвращать только прошедшие модерацию отзывы.
                Витрина использует `True`, очередь модерации — `False`.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка отзывов и общего количества записей.
        """
        conditions = [Review.product_id == product_id]
        if only_approved:
            conditions.append(Review.is_approved.is_(True))

        items_stmt = (
            select(Review)
            .where(*conditions)
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(Review).where(*conditions)

        items = (await self._session.execute(items_stmt)).scalars().all()
        total = (await self._session.execute(total_stmt)).scalar_one()
        return items, total

    async def get_average_rating(self, product_id: uuid.UUID) -> float | None:
        """Возвращает средний рейтинг товара по опубликованным отзывам.

        Args:
            product_id: Идентификатор товара.

        Returns:
            Средний рейтинг или `None`, если опубликованных отзывов нет.
        """
        stmt = select(func.avg(Review.rating)).where(
            Review.product_id == product_id,
            Review.is_approved.is_(True),
        )
        result = await self._session.execute(stmt)
        average = result.scalar_one()
        return float(average) if average is not None else None

    async def create(self, review: Review) -> Review:
        """Добавляет отзыв в сессию.

        Args:
            review: Заполненный ORM-объект отзыва.

        Returns:
            Тот же объект с заполненной меткой `created_at`.
        """
        self._session.add(review)
        await self._session.flush()
        await self._session.refresh(review)
        return review

    async def set_approved(self, review: Review, is_approved: bool) -> Review:
        """Меняет статус публикации отзыва.

        Args:
            review: Существующий ORM-объект отзыва.
            is_approved: Новое значение флага публикации.

        Returns:
            Обновлённый ORM-объект отзыва.
        """
        review.is_approved = is_approved
        await self._session.flush()
        await self._session.refresh(review)
        return review

    async def delete_by_id(self, review_id: uuid.UUID) -> bool:
        """Физически удаляет отзыв.

        Args:
            review_id: Идентификатор отзыва.

        Returns:
            `True`, если запись была удалена; `False`, если её не было.
        """
        stmt = (
            delete(Review)
            .where(Review.review_id == review_id)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount == 1
