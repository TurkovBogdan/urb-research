"""research: research_source_query table

Creates ``research_source_query`` — источниковый запрос (связь research + area + web_search-прогон,
+ синтез-вывод в ``body``). Column order mirrors ``models/source_query.py::ResearchSourceQuery``.
String PK ``code``; FK research_code/area_code (CASCADE); ``search_code`` — мягкая cross-module
soft-ref на web_search_query.code (без FK). ``unique(area_code, search_code)``.

Revision ID: rem_004_source_query
Revises: rem_003_note
Create Date: 2026-07-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "rem_004_source_query"
down_revision: Union[str, None] = "rem_003_note"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "research_source_query",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("research_code", sa.String(length=25), nullable=False),
        sa.Column("area_code", sa.String(length=25), nullable=False),
        sa.Column("search_code", sa.String(length=25), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.ForeignKeyConstraint(["research_code"], ["research_index.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["area_code"], ["research_area.code"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "area_code", "search_code", name="uq_research_source_query_area_search"
        ),
    )
    op.create_index(
        "ix_research_source_query_research_code", "research_source_query", ["research_code"]
    )
    op.create_index(
        "ix_research_source_query_area_code", "research_source_query", ["area_code"]
    )


def downgrade() -> None:
    op.drop_index("ix_research_source_query_area_code", table_name="research_source_query")
    op.drop_index(
        "ix_research_source_query_research_code", table_name="research_source_query"
    )
    op.drop_table("research_source_query")
