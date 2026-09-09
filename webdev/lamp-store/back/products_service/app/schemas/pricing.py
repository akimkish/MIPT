# products_service/app/schemas/pricing.py
"""Схемы расчёта цен корзины для internal-эндпоинта.

Отдельный модуль, а не дописка в schemas/stock.py: складские операции
меняют остатки, расчёт цен — нет, и смешивать их в одном файле значит
через месяц не помнить, какая схема к какому эндпоинту относится.

Имя PriceQuote занято NamedTuple'ом в services/catalog.py, поэтому
схемы называются CartQuote*.
"""

import uuid
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CartItemIn(BaseModel):
    """Позиция корзины во входящем запросе."""

    model_config = ConfigDict(frozen=True)

    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CartQuoteRequest(BaseModel):
    """Тело запроса на расчёт цен корзины.

    Количества обязательны: скидка зависит от `promos.min_quantity`,
    и без них расчёт вернул бы цену при qty=1, отличную от цены заказа.
    """

    model_config = ConfigDict(frozen=True)

    items: list[CartItemIn] = Field(min_length=1)

    @model_validator(mode="after")
    def check_unique_products(self) -> Self:
        """Запрещает повторы товара в корзине.

        Сервис складывает позиции в словарь «товар → количество», и дубль
        молча потерялся бы. Тот же запрет стоит в `StockService.reserve`,
        так что расхождения между расчётом и списанием не будет.

        Returns:
            Проверенный объект запроса.

        Raises:
            ValueError: Если товар встречается больше одного раза.
        """
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Товар не может встречаться в корзине дважды")
        return self


class CartQuoteOut(BaseModel):
    """Цена и снимок одной позиции корзины.

    Набор полей совпадает с тем, что orders_service копирует в
    `order_items`: этот ответ — единственный источник названия, артикула
    и цены для заказа.

    Недоступный товар не приводит к 404 на всю корзину: возвращается
    `is_available=False`, и вызывающая сторона сама решает, показать это
    пользователю или отказать в оформлении.
    """

    model_config = ConfigDict(frozen=True)

    product_id: uuid.UUID
    is_available: bool
    product_name: str | None = None
    sku: str | None = None
    image_url: str | None = None
    quantity_available: int | None = None
    original_unit_price: Decimal | None = None
    unit_price: Decimal | None = None
    promo_id: uuid.UUID | None = None


class CartQuoteListOut(BaseModel):
    """Ответ на расчёт цен корзины: по строке на каждую запрошенную позицию."""

    model_config = ConfigDict(frozen=True)

    items: list[CartQuoteOut]