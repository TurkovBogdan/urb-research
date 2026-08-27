"""research: research_index.group_code

Adds ``research_index.group_code`` — nullable FK → ``research_group.code`` (``SET NULL``): полка,
на которой лежит исследование, ``NULL`` = не разложено. Существующие строки получают ``NULL``,
бэкфилла нет. Физически колонка ложится в хвост таблицы, логический порядок — сразу после ``code``,
как в ``models/research.py::Research``.

``batch_alter_table`` обязателен: на SQLite alembic не умеет ALTER-ить constraint'ы, а обычный
``op.add_column`` с ``ForeignKey`` сначала коммитит колонку (DDL там нетранзакционный) и только
потом падает на constraint'е — миграция остаётся применённой наполовину. Batch пересоздаёт таблицу
копированием, поэтому FK получают оба бэкенда; на PostgreSQL это обычный ALTER без пересборки.

Revision ID: rem_007_research_group_code
Revises: rem_006_group
Create Date: 2026-08-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "rem_007_research_group_code"
down_revision: Union[str, None] = "rem_006_group"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK = "fk_research_index_group_code"


def upgrade() -> None:
    with op.batch_alter_table("research_index") as batch_op:
        batch_op.add_column(sa.Column("group_code", sa.String(length=25), nullable=True))
        batch_op.create_foreign_key(
            _FK, "research_group", ["group_code"], ["code"], ondelete="SET NULL"
        )
    op.create_index("ix_research_index_group_code", "research_index", ["group_code"])


def downgrade() -> None:
    op.drop_index("ix_research_index_group_code", table_name="research_index")
    with op.batch_alter_table("research_index") as batch_op:
        batch_op.drop_constraint(_FK, type_="foreignkey")
        batch_op.drop_column("group_code")
