"""core: task logs table (core_tasks_logs)

Creates ``core_tasks_logs`` — log lines for a ``core_tasks`` run. Column order
mirrors ``src/core/models/tasks.py::CoreTaskLog``. ``message`` is ``String(1024)``
(the historical Text→String(1024) narrowing is folded in here).

Revision ID: com_002_tasks_logs
Revises: com_001_tasks
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "com_002_tasks_logs"
down_revision: Union[str, None] = "com_001_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()
_TASK_LOG_LEVEL = sa.Enum(
    "debug", "info", "warn", "error",
    name="core_task_log_level", native_enum=False, length=8,
)


def upgrade() -> None:
    op.create_table(
        "core_tasks_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("core_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", _TASK_LOG_LEVEL, nullable=False),
        sa.Column("message", sa.String(length=1024), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
    )
    op.create_index("ix_core_tasks_logs_task_id", "core_tasks_logs", ["task_id"])
    op.create_index("ix_core_tasks_logs_created_at", "core_tasks_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_core_tasks_logs_created_at", table_name="core_tasks_logs")
    op.drop_index("ix_core_tasks_logs_task_id", table_name="core_tasks_logs")
    op.drop_table("core_tasks_logs")
