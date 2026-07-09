"""core: module settings table (core_modules_settings)

Creates ``core_modules_settings`` — runtime user-tunable parameters per module.
Column order mirrors ``src/core/models/module_settings.py::CoreModuleSetting``.

Revision ID: com_004_modules_settings
Revises: com_003_locks
Create Date: 2026-06-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "com_004_modules_settings"
down_revision: Union[str, None] = "com_003_locks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "core_modules_settings",
        sa.Column("module", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("core_modules_settings")
