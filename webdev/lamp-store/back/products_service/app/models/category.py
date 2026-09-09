"""ORM-модель категории товаров каталога."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Boolean, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Category(Base):
    """Категория товаров (например, «Светодиодные лампы»).

    Attributes:
        category_id: Первичный ключ (UUID4), генерируется в Python.
        name: Название категории. Уникальность обеспечена функциональным
            индексом по `lower(name)`, а не обычным UNIQUE, чтобы "LED"
            и "led" считались одним и тем же названием.
        description: Необязательное описание категории.
        is_active: Видимость на витрине. Физическое удаление категорий
            запрещено доменными правилами; к тому же товары ссылаются на
            категорию через `ON DELETE RESTRICT`, так что строку и не
            получится удалить, пока есть хоть один товар.
        created_at: Момент создания записи.
        updated_at: Момент последнего обновления записи.
        products: Товары, относящиеся к категории.
    """

    __tablename__ = "categories"

    category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    products: Mapped[list["Product"]] = relationship(back_populates="category")

    __table_args__ = (Index("ix_categories_name_lower", func.lower(name), unique=True),)

    def __repr__(self) -> str:
        """Возвращает краткое представление объекта для логов и отладки."""
        return f"Category(id={self.category_id!r}, name={self.name!r})"
