"""Pydantic-схемы отзывов на товар."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ReviewBase(BaseModel):
    """Поля отзыва, общие для создания и чтения.

    Attributes:
        user_name: Имя автора отзыва (аккаунтов покупателей в проекте нет).
        user_email: Email автора. Нормализуется в нижний регистр здесь же,
            на границе API, чтобы в репозиторий и в UNIQUE-проверку
            `(product_id, user_email)` всегда попадало каноничное значение.
        description: Необязательный текст отзыва.
        rating: Оценка от 1 до 5.
    """

    user_name: str = Field(..., min_length=1, max_length=100)
    user_email: EmailStr
    description: str | None = Field(default=None)
    rating: int = Field(..., ge=1, le=5)

    @field_validator("user_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Приводит email к нижнему регистру.

        Args:
            value: Email, введённый пользователем.

        Returns:
            Email в нижнем регистре.
        """
        return value.lower()


class ReviewCreate(ReviewBase):
    """Данные для создания отзыва.

    Attributes:
        product_id: Товар, к которому относится отзыв.
    """

    product_id: uuid.UUID


class ReviewModerate(BaseModel):
    """Данные для модерации отзыва (вызывается из admin_service).

    Отдельная узкая схема вместо переиспользования `ReviewCreate`/общего
    `Update` подчёркивает, что это единственное разрешённое изменение
    отзыва после создания — сам текст и рейтинг неизменяемы.

    Attributes:
        is_approved: Публиковать отзыв на витрине или нет.
    """

    is_approved: bool


class ReviewRead(ReviewBase):
    """Отзыв в ответах API."""

    model_config = ConfigDict(from_attributes=True)

    review_id: uuid.UUID
    product_id: uuid.UUID
    is_approved: bool
    created_at: datetime
