"""research: research_area table

Creates ``research_area`` — направление/раздел внутри исследования, знаниевый под-артефакт по
паттерну title/description/body. Column order mirrors ``models/area.py::ResearchArea``. String PK
``code``; FK ``research_code`` → research_index.code (CASCADE). Brief columns
``objective``/``scope``/``expectations`` sit before ``body``; ``sort`` was dropped during design.

Revision ID: rem_002_area
Revises: rem_001_research
Create Date: 2026-07-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "rem_002_area"
down_revision: Union[str, None] = "rem_001_research"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "research_area",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("research_code", sa.String(length=25), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False, server_default=sa.text("''")),
        sa.Column("objective", sa.String(length=1024), nullable=False, server_default=sa.text("''")),
        sa.Column("scope", sa.String(length=1024), nullable=False, server_default=sa.text("''")),
        sa.Column("expectations", sa.String(length=1024), nullable=False, server_default=sa.text("''")),
        sa.Column("body", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.ForeignKeyConstraint(["research_code"], ["research_index.code"], ondelete="CASCADE"),
    )
    op.create_index("ix_research_area_research_code", "research_area", ["research_code"])


def downgrade() -> None:
    op.drop_index("ix_research_area_research_code", table_name="research_area")
    op.drop_table("research_area")
