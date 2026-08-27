"""research: research_group table

Creates ``research_group`` — справочник для раскладки исследований (title/description/icon
+ color + sort, больший sort = выше). Имена иконки и цвета — из палитр ``icons.py`` / ``colors.py``,
в БД не валидируются. Column order mirrors ``models/group.py::ResearchGroup``. String PK
``code`` (голый 22-hex, префикс ``GROUP@`` — презентация). Ссылку с исследования (колонка
``research_index.group_code``) добавляет следующая миграция — таблица создаётся первой, чтобы
FK было на что смотреть.

Revision ID: rem_006_group
Revises: rem_005_source_document
Create Date: 2026-08-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from src.core.database.types import timestamp
from src.modules.research.constants import GROUP_SORT_DEFAULT

revision: str = "rem_006_group"
down_revision: Union[str, None] = "rem_005_source_document"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = timestamp()


def upgrade() -> None:
    op.create_table(
        "research_group",
        sa.Column("code", sa.String(length=25), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False, server_default=sa.text("''")),
        sa.Column("icon", sa.String(length=64), nullable=False, server_default=sa.text("''")),
        sa.Column("color", sa.String(length=32), nullable=False, server_default=sa.text("''")),
        sa.Column("sort", sa.Integer(), nullable=False, server_default=sa.text(str(GROUP_SORT_DEFAULT))),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("research_group")
