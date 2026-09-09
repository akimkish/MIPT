"""Начальная схема orders_service: orders, order_items.

Revision ID: 0001
Revises:
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт таблицы `orders` и `order_items` со всеми ограничениями.

    Порядок создания важен: `order_items` ссылается на `orders` через
    FK с `ON DELETE CASCADE`, поэтому таблица заказов должна
    существовать первой.
    """
    op.create_table(
        "orders",
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("user_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("delivery_address", sa.String(length=500), nullable=False),
        sa.Column(
            "total_price",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("order_id", name="pk_orders"),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_orders_idempotency_key"
        ),
        sa.CheckConstraint(
            "total_price >= 0", name="total_price_non_negative"
        ),
        sa.CheckConstraint(
            "status IN ('pending','failed','new','paid','shipped',"
            "'completed','cancelled')",
            name="status_allowed",
        ),
    )
    op.create_index("ix_orders_email", "orders", ["email"])
    op.create_index(
        "ix_orders_status_created_at", "orders", ["status", "created_at"]
    )
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "order_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "external_product_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("item_quantity", sa.Integer(), nullable=False),
        sa.Column(
            "original_unit_price", sa.Numeric(10, 2), nullable=False
        ),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "promo_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("item_id", name="pk_order_items"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.order_id"],
            name="fk_order_items_order_id_orders",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "order_id",
            "external_product_id",
            name="uq_order_item_product",
        ),
        sa.CheckConstraint(
            "item_quantity > 0", name="item_quantity_positive"
        ),
        sa.CheckConstraint(
            "original_unit_price >= 0",
            name="original_unit_price_non_negative",
        ),
        sa.CheckConstraint(
            "unit_price >= 0", name="unit_price_non_negative"
        ),
        sa.CheckConstraint(
            "unit_price <= original_unit_price",
            name="unit_price_not_above_original",
        ),
        sa.CheckConstraint(
            "total_price >= 0", name="total_price_non_negative_item"
        ),
    )


def downgrade() -> None:
    """Откатывает миграцию, удаляя таблицы в обратном порядке создания.

    `order_items` удаляется первой из-за FK на `orders` —
    `op.drop_table` для `orders` иначе упал бы на зависимой таблице.
    """
    op.drop_table("order_items")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status_created_at", table_name="orders")
    op.drop_index("ix_orders_email", table_name="orders")
    op.drop_table("orders")