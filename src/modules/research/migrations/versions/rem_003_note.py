"""research: research_note table

Creates ``research_note`` — типизированная заметка (свободная рабочая память исследования),
мини-артефакт title/description/body + обязательный ``kind`` (CHECK). Column order mirrors
``models/note.py::ResearchNote``. String PK ``code``; FK ``research_code`` → research_index.code
(CASCADE). Squashed final shape: ``kind`` CHECK already includes the sixth kind ``clarification``.

Revision ID: rem_003_note
Revises: rem_002_area
Create Date: 2026-07-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp

revision: str = "rem_003_note"
down_revision: Union[str, None] = "rem_002_area"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "research_note",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("research_code", sa.String(length=25), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False, server_default=sa.text("''")),
        sa.Column("body", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.ForeignKeyConstraint(["research_code"], ["research_index.code"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "kind IN ('result', 'idea', 'question', 'memory', 'decision', 'clarification')",
            name="ck_research_note_kind",
        ),
    )
    op.create_index("ix_research_note_research_code", "research_note", ["research_code"])


def downgrade() -> None:
    op.drop_index("ix_research_note_research_code", table_name="research_note")
    op.drop_table("research_note")
