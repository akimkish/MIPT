"""Pydantic-схемы заказа и его представлений."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import OrderStatus
from app.schemas.order_item import OrderItemRead


class OrderItemCreate(BaseModel):
    """Позиция, которую клиент указывает при оформлении заказа.

    Содержит только то, что известно клиенту — товар и количество.
    Цены (`unit_price`, `original_unit_price`, `total_price`) сюда не
    входят: их вычисляет products_service по актуальным данным
    каталога и акциям в момент оформления (Этап 7, интеграция), а не
    клиент — иначе покупатель мог бы прислать произвольную цену.

    Attributes:
        external_product_id: Идентификатор товара в products_service.
        item_quantity: Желаемое количество единиц товара, > 0.
    """

    external_product_id: uuid.UUID
    item_quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    """Данные для оформления заказа, присылаемые клиентом.

    Эндпоинт `POST /orders`, который принимает эту схему, на текущем
    этапе не реализуется (требует вызовов products_service — Этап 7),
    но сама форма входных данных фиксируется уже сейчас, так как
    зависит только от домена orders_service.

    `total_price` и `status` в схему намеренно не входят: итоговая
    сумма — это сумма позиций, а начальный статус — решение сервисного
    слоя, а не выбор клиента.

    Attributes:
        idempotency_key: Ключ идемпотентности повторной отправки формы
            заказа, уникален в рамках сервиса.
        user_name: Имя покупателя.
        phone: Контактный телефон.
        email: Контактный email. Нормализуется в нижний регистр здесь
            же, на границе API, чтобы в БД и последующий поиск по
            `email` всегда попадала уже приведённая строка.
        delivery_address: Адрес доставки.
        items: Список позиций заказа, минимум одна.
    """

    idempotency_key: str = Field(..., min_length=1, max_length=64)
    user_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: EmailStr = Field(..., max_length=255)
    delivery_address: str = Field(..., min_length=1, max_length=500)
    items: list[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Приводит email к нижнему регистру.

        Args:
            value: Email в исходном регистре, как ввёл пользователь.

        Returns:
            Email в нижнем регистре.
        """
        return value.lower()


class OrderStatusUpdate(BaseModel):
    """Данные для смены статуса заказа отдельным узким эндпоинтом.

    Вынесена в отдельную схему, а не в общий `OrderUpdate`: по
    service_context отдельного `OrderUpdate` нет вовсе — заказ вне
    смены статуса не редактируется (адрес, телефон и позиции — снимок
    на момент оформления). Допустимость конкретного перехода между
    статусами (например, `paid` → `shipped`, но не `shipped` → `new`)
    схема не проверяет — это бизнес-правило сервисного слоя, а не
    формата данных.

    Attributes:
        status: Новый статус заказа.
    """

    status: OrderStatus


class OrderRead(BaseModel):
    """Заказ в ответах API с вложенным списком позиций.

    Единая схема для списка и детали заказа (отдельного "лёгкого"
    представления без позиций не заводим): заказов у покупателя мало,
    а разработчику фронтенда удобнее получать одинаковую форму объекта
    в обоих эндпоинтах, не делая для карточки заказа второй запрос.

    Attributes:
        order_id: Идентификатор заказа.
        idempotency_key: Ключ идемпотентности, с которым создан заказ.
        user_name: Имя покупателя.
        phone: Контактный телефон.
        email: Контактный email.
        delivery_address: Адрес доставки.
        total_price: Итоговая сумма заказа, >= 0.
        status: Текущий статус заказа.
        created_at: Момент создания заказа.
        updated_at: Момент последнего обновления заказа.
        items: Позиции заказа.
    """

    model_config = ConfigDict(from_attributes=True)

    order_id: uuid.UUID
    idempotency_key: str
    user_name: str
    phone: str
    email: str
    delivery_address: str
    total_price: Decimal = Field(..., ge=0)
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]