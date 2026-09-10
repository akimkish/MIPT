import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.repositories.product import ProductRepository
from app.repositories.review import ReviewRepository
from app.schemas.review import ReviewCreate
from app.services.exceptions import ConflictError, NotFoundError


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ReviewRepository(session)
        self._products = ProductRepository(session)

    async def list_for_product(
        self,
        product_id: uuid.UUID,
        *,
        only_approved: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Review], int]:
        """Возвращает страницу отзывов на товар.

        Args:
            product_id: Идентификатор товара.
            only_approved: Возвращать только опубликованные отзывы.
                Витрина использует `True`, очередь модерации — `False`.
            limit: Размер страницы.
            offset: Смещение от начала выборки.

        Returns:
            Кортеж из списка отзывов и их общего количества.

        """
        if await self._products.get_by_id(product_id) is None:
            raise NotFoundError(f"Товар {product_id} не найден")

        return await self._repository.list_by_product(
            product_id, only_approved=only_approved, limit=limit, offset=offset
        )

    async def create(self, data: ReviewCreate) -> Review:
        """Создаёт отзыв со статусом «на модерации».

        Args:
            data: Данные отзыва (email уже нормализован схемой).

        Returns:
            Созданный отзыв.

        """
        product = await self._products.get_by_id(data.product_id)
        if product is None or not product.is_active:
            raise NotFoundError(f"Товар {data.product_id} не найден")

        duplicate = await self._repository.get_by_product_and_email(
            data.product_id, data.user_email
        )
        if duplicate is not None:
            raise ConflictError("Вы уже оставляли отзыв на этот товар")

        review = Review(**data.model_dump())
        await self._repository.create(review)
        await self._session.commit()
        return review

    async def set_approved(self, review_id: uuid.UUID, is_approved: bool) -> Review:
        """Публикует отзыв или снимает его с публикации.

        Args:
            review_id: Идентификатор отзыва.
            is_approved: Новое значение флага публикации.

        Returns:
            Обновлённый отзыв.

        """
        review = await self._repository.get_by_id(review_id)
        if review is None:
            raise NotFoundError(f"Отзыв {review_id} не найден")

        await self._repository.set_approved(review, is_approved)
        await self._session.commit()
        return review

    async def delete(self, review_id: uuid.UUID) -> None:
        """Физически удаляет отзыв.

        Args:
            review_id: Идентификатор отзыва.

        Raises:
            NotFoundError: Если отзыв не найден.
        """
        deleted = await self._repository.delete_by_id(review_id)
        if not deleted:
            raise NotFoundError(f"Отзыв {review_id} не найден")
        await self._session.commit()

    async def get_average_rating(self, product_id: uuid.UUID) -> float | None:
        """Возвращает средний рейтинг товара по опубликованным отзывам.

        Args:
            product_id: Идентификатор товара.

        Returns:
            Средний рейтинг или `None`, если отзывов нет.
        """
        return await self._repository.get_average_rating(product_id)
