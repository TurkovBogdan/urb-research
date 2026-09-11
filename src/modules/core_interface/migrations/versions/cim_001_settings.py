"""core_interface: core_interface_settings table

Creates ``core_interface_settings`` — настройки интерфейса пользователя (тема, гарнитуры,
зона чтения, схемы, раскладки списков). Строка = отклонение от умолчания; сами умолчания
объявлены в ``registry.py`` и в базу не пишутся. Column order mirrors
``src/modules/core_interface/models.py::InterfaceSetting``.

Revision ID: cim_001_settings
Revises:
Create Date: 2026-09-07
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import json_value, timestamp

revision: str = "cim_001_settings"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "core_interface_settings",
        sa.Column("key", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("value", json_value(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("core_interface_settings")
