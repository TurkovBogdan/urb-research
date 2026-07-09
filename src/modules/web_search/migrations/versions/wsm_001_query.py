"""web_search: web_search_query table

Creates ``web_search_query`` — один прогон поиска (NL) через движок.
Column order mirrors ``src/modules/web_search/models/query.py::WebSearchQuery``.
Primary key is a bare 22-hex string code (no numeric id, no prefix). No retry machinery.

Revision ID: wsm_001_query
Revises:
Create Date: 2026-07-01
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import json_value, timestamp

revision: str = "wsm_001_query"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "web_search_query",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("search_engine", sa.String(length=64), nullable=False),
        sa.Column("fetch_engine", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("params", json_value(), nullable=True),
        sa.Column("error", sa.String(length=64), nullable=True),
        sa.Column("finished_at", _TS, nullable=True),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'done', 'error')",
            name="ck_web_search_query_status",
        ),
    )
    op.create_index(
        "ix_web_search_query_engine_status", "web_search_query", ["search_engine", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_web_search_query_engine_status", table_name="web_search_query")
    op.drop_table("web_search_query")
