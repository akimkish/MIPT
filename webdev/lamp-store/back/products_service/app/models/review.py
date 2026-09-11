import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Review(Base):
    """Отзыв покупателя на товар.

    Attributes:
        review_id: Первичный ключ (UUID4), генерируется в Python.
        product_id: FK на `products`, `ON DELETE RESTRICT`.
        user_name: Имя автора (аккаунтов покупателей в проекте нет).
        user_email: Email автора. Нормализация в нижний регистр — в
            сервисном слое перед сохранением/поиском, не в этой модели.
        description: Необязательный текст отзыва.
        rating: Оценка от 1 до 5.
        is_approved: Публикуется на витрине только после модерации в
            admin_service.
        created_at: Момент создания записи.
        product: Связанный товар.
    """

    __tablename__ = "reviews"

    review_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    is_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
        UniqueConstraint(
            "product_id", "user_email", name="uq_reviews_product_id_user_email"
        ),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return (
            f"Review(id={self.review_id!r}, product_id={self.product_id!r}, "
            f"rating={self.rating!r})"
        )
