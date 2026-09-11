"""research: индексы на дочерние ключи research_source_document

``research_code`` и ``area_code`` — колонки внешних ключей, по которым индекса не было:
из трёх ключей таблицы индексирован был только ``query_code``. Движок ищет по дочернему
ключу на каждой удаляемой родительской строке, поэтому без индекса каждое удаление
исследования или области сканирует таблицу источников целиком — сейчас этим сканом платят
ручные каскады в CRUD, а после включения ``PRAGMA foreign_keys`` за то же возьмётся движок.

Revision ID: rem_010_source_doc_fk_indexes
Revises: rem_009_research_desc_width
Create Date: 2026-09-06
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "rem_010_source_doc_fk_indexes"
down_revision: Union[str, None] = "rem_009_research_desc_width"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "research_source_document"
_INDEXED_FOREIGN_KEYS = ("research_code", "area_code")


def upgrade() -> None:
    for column in _INDEXED_FOREIGN_KEYS:
        op.create_index(f"ix_{_TABLE}_{column}", _TABLE, [column])


def downgrade() -> None:
    for column in _INDEXED_FOREIGN_KEYS:
        op.drop_index(f"ix_{_TABLE}_{column}", table_name=_TABLE)
