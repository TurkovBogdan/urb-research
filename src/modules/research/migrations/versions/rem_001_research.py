"""research: research_index table

Creates ``research_index`` — исследование (корень реестра), знаниевый артефакт.
Column order mirrors ``src/modules/research/models/research.py::Research``.
String PK ``code`` (bare 22-hex hash); ``title``/``description``/``body`` content.
No status. Root of area / note / source_query / source_document. No cross-module FK.

Revision ID: rem_001_research
Revises:
Create Date: 2026-07-05
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "rem_001_research"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "research_index",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False, server_default=sa.text("''")),
        sa.Column("body", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("research_index")
