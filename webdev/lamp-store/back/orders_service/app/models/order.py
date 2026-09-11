import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import OrderStatus

if TYPE_CHECKING:
    from app.models.order_item import OrderItem


class Order(Base):
    """Заказ покупателя.

    Attributes:
        order_id: Первичный ключ (UUID4), генерируется в Python.
        idempotency_key: Ключ идемпотентности запроса создания заказа,
            уникален в рамках сервиса.
        user_name: Имя покупателя, указанное при оформлении.
        phone: Контактный телефон.
        email: Контактный email. Нормализуется в нижний регистр перед
            сохранением и перед поиском на уровне репозитория.
        delivery_address: Адрес доставки.
        total_price: Итоговая сумма заказа, >= 0. Равна сумме
            `total_price` всех позиций; пересчитывается в сервисном
            слое при создании заказа (Этап 7), здесь не вычисляется.
        status: Статус заказа. Хранится как `String(20)` с CHECK по
            списку значений `OrderStatus` (нативный ENUM PostgreSQL не
            используется).
        created_at: Момент создания записи.
        updated_at: Момент последнего обновления записи.
        items: Позиции заказа.
    """

    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0"), server_default="0"
    )
    status: Mapped[OrderStatus] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")

    __table_args__ = (
        CheckConstraint("total_price >= 0", name="total_price_non_negative"),
        CheckConstraint(
            "status IN ('pending','failed','new','paid','shipped',"
            "'completed','cancelled')",
            name="status_allowed",
        ),
        Index("ix_orders_email", "email"),
        Index("ix_orders_status_created_at", "status", "created_at"),
        Index("ix_orders_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return f"Order(id={self.order_id!r}, status={self.status!r})"
