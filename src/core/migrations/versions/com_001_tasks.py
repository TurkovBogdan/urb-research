"""core: tasks table (core_tasks)

Creates ``core_tasks`` — one row per background-task run. Column order mirrors
``src/core/models/tasks.py::CoreTask``.

First migration of the core chain; one table per migration keeps each
table-creating revision a non-head once its successor lands, so cross-module
migrations (e.g. ``cum_004_task_requests``) can ``depends_on = "com_001_tasks"``
for their FK to ``core_tasks.id`` (see AGENTS/docs/conventions/db-migrations.md).

Revision ID: com_001_tasks
Revises:
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "com_001_tasks"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()
_TASK_STATUS = sa.Enum(
    "running", "success", "error",
    name="core_task_status", native_enum=False, length=16,
)


def upgrade() -> None:
    op.create_table(
        "core_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("status", _TASK_STATUS, nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("error_text", sa.String(length=512), nullable=True),
        sa.Column("started_at", _TS, nullable=False),
        sa.Column("heartbeat_at", _TS, nullable=True),
        sa.Column("finished_at", _TS, nullable=True),
    )
    op.create_index("ix_core_tasks_status", "core_tasks", ["status"])
    op.create_index("ix_core_tasks_module_code", "core_tasks", ["module", "code"])
    op.create_index("ix_core_tasks_started_at", "core_tasks", ["started_at"])
    op.create_index(
        "uq_core_tasks_running_pair",
        "core_tasks",
        ["module", "code"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
        sqlite_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    op.drop_index("uq_core_tasks_running_pair", table_name="core_tasks")
    op.drop_index("ix_core_tasks_started_at", table_name="core_tasks")
    op.drop_index("ix_core_tasks_module_code", table_name="core_tasks")
    op.drop_index("ix_core_tasks_status", table_name="core_tasks")
    op.drop_table("core_tasks")
