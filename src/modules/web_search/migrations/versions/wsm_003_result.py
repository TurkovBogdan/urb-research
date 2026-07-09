"""web_search: web_search_query_result table

Creates ``web_search_query_result`` — результаты запроса (связь запрос ↔ документ).
Column order mirrors
``src/modules/web_search/models/query_result.py::WebSearchQueryResult``.
Surrogate int ``id``; FKs to string codes ``query_code`` → web_search_query.code,
``page_code`` → web_search_page.code. Ordering held by down_revision, no depends_on.

Revision ID: wsm_003_result
Revises: wsm_002_page
Create Date: 2026-07-01
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import json_value, timestamp

revision: str = "wsm_003_result"
down_revision: Union[str, None] = "wsm_002_page"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "web_search_query_result",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("query_code", sa.String(length=25), nullable=False),
        sa.Column("page_code", sa.String(length=25), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("meta", json_value(), nullable=True),
        sa.Column("created_at", _TS, nullable=False),
        sa.ForeignKeyConstraint(["query_code"], ["web_search_query.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["page_code"], ["web_search_page.code"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "query_code", "page_code", name="uq_web_search_query_result_query_page"
        ),
    )
    op.create_index(
        "ix_web_search_query_result_query_code",
        "web_search_query_result",
        ["query_code"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_web_search_query_result_query_code",
        table_name="web_search_query_result",
    )
    op.drop_table("web_search_query_result")
