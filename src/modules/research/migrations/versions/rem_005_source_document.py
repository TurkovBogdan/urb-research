"""research: research_source_document table

Creates ``research_source_document`` — источник: ссылка на найденную страницу + research-оценка
(не копия — url/domain/title/body джойнятся из web_search_page по ``page_code``). Column order
mirrors ``models/source_document.py::ResearchSourceDocument``. String PK ``code``; FK
research_code/area_code/query_code (CASCADE); ``page_code`` — soft-ref на web_search_page (без FK).
``unique(query_code, page_code)``; CHECK status + CHECK relevance 1–10.

Revision ID: rem_005_source_document
Revises: rem_004_source_query
Create Date: 2026-07-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "rem_005_source_document"
down_revision: Union[str, None] = "rem_004_source_query"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "research_source_document",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("research_code", sa.String(length=25), nullable=False),
        sa.Column("area_code", sa.String(length=25), nullable=False),
        sa.Column("query_code", sa.String(length=25), nullable=False),
        sa.Column("page_code", sa.String(length=25), nullable=False),
        sa.Column(
            "status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")
        ),
        sa.Column("relevance", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("note", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.ForeignKeyConstraint(["research_code"], ["research_index.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["area_code"], ["research_area.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["query_code"], ["research_source_query.code"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "query_code", "page_code", name="uq_research_source_document_query_page"
        ),
        sa.CheckConstraint(
            "status IN ('fetch_error', 'pending', 'kept', 'filtered')",
            name="ck_research_source_document_status",
        ),
        sa.CheckConstraint(
            "relevance BETWEEN 1 AND 10", name="ck_research_source_document_relevance"
        ),
    )
    op.create_index(
        "ix_research_source_document_query_code",
        "research_source_document",
        ["query_code"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_research_source_document_query_code", table_name="research_source_document"
    )
    op.drop_table("research_source_document")
