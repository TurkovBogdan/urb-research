"""core_connectors: core_connectors_access table

Creates ``core_connectors_access`` — запись доступа к внешнему сервису (чем мы туда ходим).
Column order mirrors ``src/modules/core_connectors/access/model.py::CoreConnectorsAccess``.
Единственная таблица модуля: паспорт коннектора живёт в коде, реестр — в памяти процесса,
мастер-ключ — в окружении, поэтому новый коннектор/поле/запись миграции не требуют.

Revision ID: ccm_001_access
Revises:
Create Date: 2026-09-05
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import json_value, timestamp

revision: str = "ccm_001_access"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "core_connectors_access",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("connector", sa.String(length=64), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("values", json_value(), nullable=False),
        sa.Column("data_key", sa.Text(), nullable=True),
        sa.Column("key_version", sa.String(length=16), nullable=True),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )
    op.create_index(
        "ix_core_connectors_access_connector", "core_connectors_access", ["connector"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_connectors_access_connector", table_name="core_connectors_access"
    )
    op.drop_table("core_connectors_access")
