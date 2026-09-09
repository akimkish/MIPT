"""Начальная миграция admin_service: таблицы admins и audit_log.

Revision ID: 0001
Revises:
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# --- Идентификаторы ревизии Alembic --------------------------------------
revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт таблицы `admins` и `audit_log`.

    Порядок важен: `audit_log.admin_id` ссылается на `admins.admin_id`,
    поэтому `admins` создаётся первой.
    """
    op.create_table(
        "admins",
        sa.Column(
            "admin_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=60), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role_name", sa.String(length=50), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "locked_until", sa.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column("last_login", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="admins_email_key"),
        sa.CheckConstraint(
            "failed_login_attempts >= 0",
            name="failed_login_attempts_non_negative",
        ),
        sa.CheckConstraint(
            "role_name IN ('superadmin','manager','moderator')",
            name="role_name_allowed",
        ),
    )
    op.create_index(
        "ix_admins_role_name", "admins", ["role_name"], unique=False
    )

    op.create_table(
        "audit_log",
        sa.Column(
            "log_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "admin_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("actor_email", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column(
            "entity_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["admins.admin_id"],
            name="audit_log_admin_id_fkey",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "action IN ('login_success','login_failed','admin_created',"
            "'admin_deactivated','role_changed')",
            name="action_allowed",
        ),
    )
    op.create_index(
        "ix_audit_log_admin_id_created_at",
        "audit_log",
        ["admin_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_log_action_created_at",
        "audit_log",
        ["action", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Удаляет `audit_log` и `admins` в порядке, обратном созданию.

    `audit_log` — первой: у неё есть FK на `admins`, `admins` без
    зависимых таблиц удаляется последней.
    """
    op.drop_index("ix_audit_log_action_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_admin_id_created_at", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_admins_role_name", table_name="admins")
    op.drop_table("admins")