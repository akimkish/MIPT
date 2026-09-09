"""ORM-модель позиции заказа."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.order import Order


class OrderItem(Base):
    """Позиция заказа — неизменяемый снимок товара на момент оформления.

    Все поля товара (название, sku, цены, картинка) копируются из
    products_service в момент создания заказа и никогда не
    обновляются — именно поэтому у модели нет `updated_at`. Связь с
    каталогом хранится только как `external_product_id` без FK: заказы
    и товары живут в разных БД разных сервисов.

    Attributes:
        item_id: Первичный ключ (UUID4), генерируется в Python.
        order_id: FK на `orders`, `ON DELETE CASCADE`.
        external_product_id: Идентификатор товара в products_service.
            Без FK — межбазовая ссылка, целостность не обеспечивается
            на уровне БД.
        product_name: Название товара на момент заказа (снимок).
        sku: Артикул товара на момент заказа (снимок).
        image_url: Ссылка на изображение товара на момент заказа
            (снимок ссылки, не копия файла — подмена файла в каталоге
            изменит картинку и в старом заказе).
        item_quantity: Количество единиц товара в позиции, > 0.
        original_unit_price: Цена за единицу до применения скидки.
        unit_price: Цена за единицу после применения скидки,
            <= original_unit_price. Скидку выбирает products_service;
            orders_service её не пересчитывает.
        promo_id: Идентификатор применённой акции, если была. Без FK
            по тем же причинам, что и `external_product_id`.
        total_price: Итог по позиции, >= 0. Равен
            `unit_price * item_quantity`.
        created_at: Момент создания записи (совпадает с моментом
            создания заказа).
        order: Родительский заказ.
    """

    __tablename__ = "order_items"

    item_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    external_product_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(32), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    original_unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    promo_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("item_quantity > 0", name="item_quantity_positive"),
        CheckConstraint(
            "original_unit_price >= 0", name="original_unit_price_non_negative"
        ),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        CheckConstraint(
            "unit_price <= original_unit_price", name="unit_price_not_above_original"
        ),
        CheckConstraint("total_price >= 0", name="total_price_non_negative_item"),
        UniqueConstraint(
            "order_id", "external_product_id", name="uq_order_item_product"
        ),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return f"OrderItem(id={self.item_id!r}, sku={self.sku!r})"
