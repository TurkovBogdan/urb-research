"""core: locks table (core_locks)

Creates ``core_locks`` — advisory locks held by the scheduler/lock manager.
This table has no ORM model; the lock manager reads/writes it directly.

Revision ID: com_003_locks
Revises: com_002_tasks_logs
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "com_003_locks"
down_revision: Union[str, None] = "com_002_tasks_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "core_locks",
        sa.Column("key", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("acquired_at", _TS, nullable=False),
        sa.Column("expires_at", _TS, nullable=False),
    )
    op.create_index("ix_core_locks_owner", "core_locks", ["owner"])
    op.create_index("ix_core_locks_expires_at", "core_locks", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_core_locks_expires_at", table_name="core_locks")
    op.drop_index("ix_core_locks_owner", table_name="core_locks")
    op.drop_table("core_locks")
