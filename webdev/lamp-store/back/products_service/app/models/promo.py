"""ORM-модель промо-акции на товар."""

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
from app.models.enums import DiscountType

if TYPE_CHECKING:
    from app.models.product import Product


class Promo(Base):
    """Промо-акция на товар: скидка при достижении `min_quantity` в окне дат.

    Attributes:
        promo_id: Первичный ключ (UUID4), генерируется в Python.
        promo_name: Название акции.
        description: Необязательное описание.
        discount_type: `percent` или `fixed`. Хранится как `String(10)`
            с CHECK по списку значений `DiscountType`.
        discount: Величина скидки; для `percent` ограничена сверху 100.
        product_id: FK на `products`, `ON DELETE RESTRICT`.
        min_quantity: Минимальное количество позиции в заказе для
            применения акции, >= 1.
        valid_from: Начало действия акции (строго раньше `valid_to`).
        valid_to: Конец действия акции.
        is_active: Ручное включение/выключение акции независимо от дат.
            Физическое удаление акций запрещено.
        created_at: Момент создания записи.
        updated_at: Момент последнего обновления записи.
        product: Связанный товар.
    """

    __tablename__ = "promos"

    promo_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    promo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(String(10), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
    )
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    valid_from: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    valid_to: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
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

    product: Mapped["Product"] = relationship(back_populates="promos")

    __table_args__ = (
        CheckConstraint("discount > 0", name="discount_positive"),
        CheckConstraint(
            "discount_type <> 'percent' OR discount <= 100",
            name="percent_discount_max_100",
        ),
        CheckConstraint("valid_from < valid_to", name="valid_from_before_valid_to"),
        CheckConstraint("min_quantity >= 1", name="min_quantity_positive"),
        CheckConstraint(
            "discount_type IN ('percent','fixed')", name="discount_type_allowed"
        ),
        Index("ix_promos_product_id_is_active", "product_id", "is_active"),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return (
            f"Promo(id={self.promo_id!r}, product_id={self.product_id!r}, "
            f"discount_type={self.discount_type!r})"
        )
