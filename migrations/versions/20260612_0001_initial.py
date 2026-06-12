"""initial schema

Revision ID: 20260612_0001
Revises:
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260612_0001"
down_revision = None
branch_labels = None
depends_on = None


recurrence_type = sa.Enum(
    "once",
    "daily",
    "weekly",
    "monthly",
    "yearly",
    name="recurrencetype",
    native_enum=False,
)
task_priority = sa.Enum(
    "low",
    "normal",
    "high",
    name="taskpriority",
    native_enum=False,
)
task_status = sa.Enum(
    "todo",
    "in_progress",
    "done",
    name="taskstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "reminder_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_reminder_categories_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_reminder_categories"),
        sa.UniqueConstraint("user_id", "title", name="uq_category_user_title"),
    )
    op.create_index("ix_reminder_categories_user_id", "reminder_categories", ["user_id"], unique=False)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("remind_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("recurrence", recurrence_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["reminder_categories.id"], name="fk_reminders_category_id_reminder_categories", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_reminders_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_reminders"),
    )
    op.create_index("ix_reminders_category_id", "reminders", ["category_id"], unique=False)
    op.create_index("ix_reminders_next_run_at", "reminders", ["next_run_at"], unique=False)
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("priority", task_priority, nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_tasks_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
    )
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_due_at", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_reminders_user_id", table_name="reminders")
    op.drop_index("ix_reminders_next_run_at", table_name="reminders")
    op.drop_index("ix_reminders_category_id", table_name="reminders")
    op.drop_table("reminders")
    op.drop_index("ix_reminder_categories_user_id", table_name="reminder_categories")
    op.drop_table("reminder_categories")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
