"""Pydantic-схемы товара и его представлений в каталоге."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SocketType
from app.schemas.category import CategoryRead
from app.schemas.manufacturer import ManufacturerRead


class ProductBase(BaseModel):
    """Поля товара, общие для создания и чтения.

    Границы значений (`ge`/`gt`/`le`) продублированы из CHECK-ограничений
    таблицы `products` (см. PROMPT_CONTEXT.md → db_schema) — это
    намеренное дублирование: Pydantic отсекает некорректные данные ещё
    до похода в БД и даёт понятную ошибку 422 вместо голого IntegrityError.

    Attributes:
        product_name: Отображаемое название товара.
        sku: Артикул, уникален в рамках каталога (проверка — в репозитории).
        category_id: Идентификатор категории.
        manufacturer_id: Идентификатор производителя.
        price: Цена за единицу, >= 0.
        quantity: Остаток на складе, >= 0. В `ProductCreate` — начальный
            остаток; далее меняется только через `services/stock.py`,
            не через обновление товара.
        description: Необязательное описание.
        power_watts: Мощность в ваттах, > 0.
        socket_type: Тип цоколя из ограниченного набора значений.
        color_temperature_k: Цветовая температура, 1000..10000 K.
        image_url: Необязательная ссылка на изображение.
    """

    product_name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=32)
    category_id: uuid.UUID
    manufacturer_id: uuid.UUID
    price: Decimal = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    description: str | None = Field(default=None)
    power_watts: Decimal = Field(..., gt=0)
    socket_type: SocketType
    color_temperature_k: int = Field(..., ge=1000, le=10000)
    image_url: str | None = Field(default=None, max_length=500)


class ProductCreate(ProductBase):
    """Данные для создания товара."""


class ProductUpdate(BaseModel):
    """Данные для частичного обновления товара (PATCH).

    `quantity` намеренно исключён: остаток меняется только атомарными
    операциями `services/stock.py` (reserve/release), а не произвольным
    PATCH — иначе легко потерять корректность при гонке с резервированием.
    """

    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=32)
    category_id: uuid.UUID | None = None
    manufacturer_id: uuid.UUID | None = None
    price: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    power_watts: Decimal | None = Field(default=None, gt=0)
    socket_type: SocketType | None = None
    color_temperature_k: int | None = Field(default=None, ge=1000, le=10000)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProductRead(ProductBase):
    """Товар в ответах API без развёрнутых связанных сущностей."""

    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductWithRelations(ProductRead):
    """Товар с развёрнутыми категорией и производителем.

    Используется там, где нужно показать название категории/бренда без
    отдельного запроса с фронтенда (например, карточка товара).
    """

    category: CategoryRead
    manufacturer: ManufacturerRead


class ProductCatalogItem(ProductRead):
    """Товар в списке витрины с учётом активных промо-акций.

    Заполняется в `services/catalog.py`, а не репозиторием напрямую —
    расчёт `display_price`/`bulk_discount_hint` требует бизнес-логики
    выбора применимой акции (см. domain_decisions → «Скидки»).

    Attributes:
        display_price: Цена за единицу при заказе qty=1 с учётом акций,
            применимых при min_quantity=1. Если такой акции нет —
            совпадает с `price`.
        bulk_discount_hint: Текст-подсказка вида «от 3 шт. дешевле», если
            есть акция с `min_quantity > 1`; иначе `None`.
    """

    display_price: Decimal = Field(..., ge=0)
    bulk_discount_hint: str | None = Field(default=None)


class ProductDetail(ProductCatalogItem):
    """Полная карточка товара для публичного эндпоинта детали.

    Объединяет витринную цену (`ProductCatalogItem`) с развёрнутыми
    категорией/производителем и средним рейтингом — тем, что нужно
    странице товара за один запрос.

    Attributes:
        category: Развёрнутая категория товара.
        manufacturer: Развёрнутый производитель товара.
        average_rating: Средний рейтинг по опубликованным отзывам;
            `None`, если отзывов ещё нет.
    """

    category: CategoryRead
    manufacturer: ManufacturerRead
    average_rating: float | None = Field(default=None)
