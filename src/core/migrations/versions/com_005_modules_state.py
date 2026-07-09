"""core: module state table (core_modules_state)

Creates ``core_modules_state`` — arbitrary per-module runtime state (JSONB:
import cursors, counters, run markers). Column order mirrors
``src/core/models/module_state.py::CoreModuleState``.

Revision ID: com_005_modules_state
Revises: com_004_modules_settings
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import json_value, timestamp

revision: str = "com_005_modules_state"
down_revision: Union[str, None] = "com_004_modules_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "core_modules_state",
        sa.Column("module", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("value", json_value(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("core_modules_state")
