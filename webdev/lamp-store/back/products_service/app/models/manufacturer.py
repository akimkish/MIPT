"""ORM-модель производителя товаров каталога."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Boolean, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Manufacturer(Base):
    """Производитель ламп (бренд).

    Attributes:
        manufacturer_id: Первичный ключ (UUID4), генерируется в Python.
        name: Название производителя, уникальное без учёта регистра
            (функциональный индекс по `lower(name)`, как у `Category`).
        description: Необязательное описание.
        logo_url: Необязательная ссылка на логотип.
        is_active: Видимость на витрине. Физическое удаление запрещено —
            товары ссылаются через `ON DELETE RESTRICT`.
        created_at: Момент создания записи.
        updated_at: Момент последнего обновления записи.
        products: Товары данного производителя.
    """

    __tablename__ = "manufacturers"

    manufacturer_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    products: Mapped[list["Product"]] = relationship(back_populates="manufacturer")

    __table_args__ = (
        Index("ix_manufacturers_name_lower", func.lower(name), unique=True),
    )

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return f"Manufacturer(id={self.manufacturer_id!r}, name={self.name!r})"
