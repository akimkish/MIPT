import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, CheckConstraint, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.enums import StockOperationType


class StockOperation(Base):
    """Запись о списании (`reserve`) или возврате (`release`) остатка по заказу.

    Attributes:
     order_id: Идентификатор заказа из orders_service.
     operation: `reserve` или `release`.
     payload: Снимок позиций заказа на момент операции (список пар
         `product_id`/`quantity`). Для `reserve` используется затем как
         источник данных для корректного `release` при отмене заказа.
     created_at: Момент записи операции.
    """

    __tablename__ = "stock_operations"

    order_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    operation: Mapped[StockOperationType] = mapped_column(String(10), primary_key=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("operation IN ('reserve','release')", name="operation_allowed"),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return (
            f"StockOperation(order_id={self.order_id!r}, "
            f"operation={self.operation!r})"
        )
