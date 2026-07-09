"""web_search: web_search_page table

Creates ``web_search_page`` — контент страницы (документ поиска).
Column order mirrors ``src/modules/web_search/models/page.py::WebSearchPage``.
Primary key is the string code (deterministic url-hash → dedup by url),
so ``web_search_query_result.page_code`` FKs to it. No numeric id, no retry machinery.
Squashed final shape: content columns are ``body`` / ``body_hash`` (the earlier
``content`` / ``content_hash`` rename is folded in).

Revision ID: wsm_002_page
Revises: wsm_001_query
Create Date: 2026-07-01
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "wsm_002_page"
down_revision: Union[str, None] = "wsm_001_query"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "web_search_page",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("fetch_engine", sa.String(length=64), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("body_hash", sa.String(length=22), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("error", sa.String(length=64), nullable=True),
        sa.Column("fetched_at", _TS, nullable=True),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'done', 'error')",
            name="ck_web_search_page_status",
        ),
    )
    op.create_index("ix_web_search_page_status", "web_search_page", ["status"])


def downgrade() -> None:
    op.drop_index("ix_web_search_page_status", table_name="web_search_page")
    op.drop_table("web_search_page")
