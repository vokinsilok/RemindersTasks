"""add vk users

Revision ID: 20260612_0002
Revises: 20260612_0001
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260612_0002"
down_revision = "20260612_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("platform", sa.String(length=32), server_default="telegram", nullable=False),
    )
    op.add_column("users", sa.Column("vk_user_id", sa.BigInteger(), nullable=True))
    op.alter_column("users", "telegram_id", existing_type=sa.BigInteger(), nullable=True)
    op.create_index("ix_users_platform", "users", ["platform"], unique=False)
    op.create_index("ix_users_vk_user_id", "users", ["vk_user_id"], unique=True)
    op.alter_column("users", "platform", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_vk_user_id", table_name="users")
    op.drop_index("ix_users_platform", table_name="users")
    op.alter_column("users", "telegram_id", existing_type=sa.BigInteger(), nullable=False)
    op.drop_column("users", "vk_user_id")
    op.drop_column("users", "platform")
