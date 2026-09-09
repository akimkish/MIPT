"""ORM-модель товара (лампы) каталога."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import SocketType

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.manufacturer import Manufacturer
    from app.models.promo import Promo
    from app.models.review import Review


class Product(Base):
    """Товар каталога — лампочка с характеристиками, ценой и остатком.

    Attributes:
        product_id: Первичный ключ (UUID4), генерируется в Python.
        product_name: Отображаемое название товара.
        sku: Артикул, уникален в рамках каталога.
        category_id: FK на `categories`, `ON DELETE RESTRICT`.
        manufacturer_id: FK на `manufacturers`, `ON DELETE RESTRICT`.
        price: Цена за единицу, >= 0.
        quantity: Остаток на складе, >= 0. Атомарно списывается/возвращается
            в `services/stock.py`; в этом слое напрямую не модифицируется.
        description: Необязательное описание.
        power_watts: Мощность в ваттах, > 0.
        socket_type: Тип цоколя. Хранится как `String(10)` с CHECK по
            списку значений `SocketType` (нативный ENUM PostgreSQL в
            проекте не используется).
        color_temperature_k: Цветовая температура в Кельвинах, 1000..10000.
        image_url: Необязательная ссылка на изображение.
        is_active: Видимость на витрине. Физическое удаление запрещено.
        created_at: Момент создания записи.
        updated_at: Момент последнего обновления записи.
        category: Связанная категория.
        manufacturer: Связанный производитель.
        reviews: Отзывы на товар.
        promos: Акции, применимые к товару.
    """

    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.category_id", ondelete="RESTRICT"),
        nullable=False,
    )
    manufacturer_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("manufacturers.manufacturer_id", ondelete="RESTRICT"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    power_watts: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    socket_type: Mapped[SocketType] = mapped_column(String(10), nullable=False)
    color_temperature_k: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="products")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
    promos: Mapped[list["Promo"]] = relationship(back_populates="product")

    __table_args__ = (
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("power_watts > 0", name="power_watts_positive"),
        CheckConstraint(
            "color_temperature_k BETWEEN 1000 AND 10000",
            name="color_temperature_k_range",
        ),
        CheckConstraint(
            "socket_type IN ('E14','E27','E40','G4','G9','G13','GU10','GU5.3')",
            name="socket_type_allowed",
        ),
        Index("ix_products_category_id_is_active", "category_id", "is_active"),
        Index("ix_products_manufacturer_id", "manufacturer_id"),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return f"Product(id={self.product_id!r}, sku={self.sku!r})"
