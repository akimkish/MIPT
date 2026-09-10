from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# --- Alembic identifiers ----------------------------------------------------
revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт все таблицы, ограничения и индексы products_service."""

    # -------------------------------------------------------------------
    # categories
    # -------------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("category_id"),
    )
    # Функциональный уникальный индекс: "LED" и "led" — одна категория.
    op.execute(
        "CREATE UNIQUE INDEX ix_categories_name_lower " "ON categories (lower(name))"
    )

    # -------------------------------------------------------------------
    # manufacturers
    # -------------------------------------------------------------------
    op.create_table(
        "manufacturers",
        sa.Column("manufacturer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("manufacturer_id"),
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_manufacturers_name_lower "
        "ON manufacturers (lower(name))"
    )

    # -------------------------------------------------------------------
    # products
    # -------------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manufacturer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "quantity", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("power_watts", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column("socket_type", sa.String(length=10), nullable=False),
        sa.Column("color_temperature_k", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("product_id"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.category_id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["manufacturer_id"],
            ["manufacturers.manufacturer_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("sku"),
        sa.CheckConstraint("price >= 0", name="price_non_negative"),
        sa.CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        sa.CheckConstraint("power_watts > 0", name="power_watts_positive"),
        sa.CheckConstraint(
            "color_temperature_k BETWEEN 1000 AND 10000",
            name="color_temperature_k_range",
        ),
        sa.CheckConstraint(
            "socket_type IN ('E14','E27','E40','G4','G9','G13','GU10','GU5.3')",
            name="socket_type_allowed",
        ),
    )
    op.create_index(
        "ix_products_category_id_is_active",
        "products",
        ["category_id", "is_active"],
    )
    op.create_index("ix_products_manufacturer_id", "products", ["manufacturer_id"])

    # -------------------------------------------------------------------
    # reviews
    # -------------------------------------------------------------------
    op.create_table(
        "reviews",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_name", sa.String(length=100), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column(
            "is_approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("review_id"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.product_id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "product_id", "user_email", name="uq_reviews_product_id_user_email"
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
    )

    # -------------------------------------------------------------------
    # promos
    # -------------------------------------------------------------------
    op.create_table(
        "promos",
        sa.Column("promo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("promo_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(length=10), nullable=False),
        sa.Column("discount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "min_quantity", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("valid_from", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("valid_to", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("promo_id"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.product_id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint("discount > 0", name="discount_positive"),
        sa.CheckConstraint(
            "discount_type <> 'percent' OR discount <= 100",
            name="percent_discount_max_100",
        ),
        sa.CheckConstraint("valid_from < valid_to", name="valid_from_before_valid_to"),
        sa.CheckConstraint("min_quantity >= 1", name="min_quantity_positive"),
        sa.CheckConstraint(
            "discount_type IN ('percent','fixed')", name="discount_type_allowed"
        ),
    )
    op.create_index(
        "ix_promos_product_id_is_active", "promos", ["product_id", "is_active"]
    )

    # -------------------------------------------------------------------
    # stock_operations
    # -------------------------------------------------------------------
    op.create_table(
        "stock_operations",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation", sa.String(length=10), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("order_id", "operation"),
        sa.CheckConstraint(
            "operation IN ('reserve','release')", name="operation_allowed"
        ),
    )


def downgrade() -> None:
    """Удаляет все таблицы products_service в порядке, обратном созданию.

    Порядок важен из-за FOREIGN KEY: reviews/promos ссылаются на products,
    products ссылается на categories/manufacturers — зависимые таблицы
    удаляются первыми.
    """
    op.drop_table("stock_operations")
    op.drop_table("promos")
    op.drop_table("reviews")
    op.drop_index("ix_products_manufacturer_id", table_name="products")
    op.drop_index("ix_products_category_id_is_active", table_name="products")
    op.drop_table("products")
    op.execute("DROP INDEX IF EXISTS ix_manufacturers_name_lower")
    op.drop_table("manufacturers")
    op.execute("DROP INDEX IF EXISTS ix_categories_name_lower")
    op.drop_table("categories")
