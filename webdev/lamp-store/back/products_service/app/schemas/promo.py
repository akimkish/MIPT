"""Pydantic-схемы промо-акций."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import DiscountType


class PromoBase(BaseModel):
    """Поля акции, общие для создания и чтения.

    Attributes:
        promo_name: Название акции.
        description: Необязательное описание.
        discount_type: `percent` или `fixed`.
        discount: Величина скидки, > 0; для `percent` дополнительно
            ограничена сверху 100 (проверяется в `check_discount_bounds`).
        product_id: Товар, к которому относится акция.
        min_quantity: Минимальное количество позиции для применения
            акции, >= 1.
        valid_from: Начало действия акции.
        valid_to: Конец действия акции (строго позже `valid_from`,
            проверяется в `check_dates_order`).
    """

    promo_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    discount_type: DiscountType
    discount: Decimal = Field(..., gt=0)
    product_id: uuid.UUID
    min_quantity: int = Field(default=1, ge=1)
    valid_from: datetime
    valid_to: datetime

    @model_validator(mode="after")
    def check_discount_bounds(self) -> "PromoBase":
        """Проверяет, что процентная скидка не превышает 100.

        Returns:
            Тот же объект, если проверка пройдена.

        Raises:
            ValueError: Если `discount_type == percent`, а `discount > 100`.
        """
        if self.discount_type == DiscountType.PERCENT and self.discount > 100:
            raise ValueError("Процентная скидка не может превышать 100")
        return self

    @model_validator(mode="after")
    def check_dates_order(self) -> "PromoBase":
        """Проверяет, что `valid_from` строго раньше `valid_to`.

        Returns:
            Тот же объект, если проверка пройдена.

        Raises:
            ValueError: Если `valid_from >= valid_to`.
        """
        if self.valid_from >= self.valid_to:
            raise ValueError("valid_from должен быть раньше valid_to")
        return self


class PromoCreate(PromoBase):
    """Данные для создания акции."""


class PromoUpdate(BaseModel):
    """Данные для частичного обновления акции (PATCH).

    Кросс-полевые проверки (`discount`/`discount_type`, порядок дат)
    здесь намеренно не выполняются: PATCH может прислать только одно из
    двух связанных полей, и корректность нужно проверять относительно
    уже сохранённых значений — это ответственность `services/`, а не
    схемы уровня одного запроса.
    """

    promo_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    discount_type: DiscountType | None = None
    discount: Decimal | None = Field(default=None, gt=0)
    min_quantity: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None


class PromoRead(PromoBase):
    """Акция в ответах API."""

    model_config = ConfigDict(from_attributes=True)

    promo_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
