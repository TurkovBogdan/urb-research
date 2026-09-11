"""research: research_index.description 512 → 2048

Колонка объявляла 512, но эту границу никто не держал: описание пишет агент через MCP, а
``crud/research.py`` — единственный CRUD модуля, который не усекал свои строки (у области,
заметки и группы усечение есть). SQLite длину VARCHAR не проверяет, поэтому расхождение копилось
молча: на момент миграции 21 исследование из 50 длиннее 512, самое длинное — 875 символов. На
PostgreSQL те же данные не записались бы вовсе.

Ширина выбрана по факту, а не по круглому числу: 2048 — это запас к нынешнему максимуму, при
котором описание остаётся кратким (тело без лимита живёт в ``body``). Заодно усечение появилось
в CRUD, поэтому граница снова одна и та же со всех сторон.

Данные не трогаем: расширение колонки существующие строки не задевает.

``batch_alter_table`` — потому что ALTER COLUMN на SQLite alembic сам не умеет; на PostgreSQL
это обычный ALTER TYPE без пересборки.

Revision ID: rem_009_research_desc_width
Revises: rem_008_source_doc_error_status
Create Date: 2026-08-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "rem_009_research_desc_width"
down_revision: Union[str, None] = "rem_008_source_doc_error_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_WAS = 512
_NOW = 2048


def _retype_description(*, was: int, now: int) -> None:
    with op.batch_alter_table("research_index") as batch_op:
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=was),
            type_=sa.String(length=now),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
        )


def upgrade() -> None:
    _retype_description(was=_WAS, now=_NOW)


def downgrade() -> None:
    """Сужение обрежет описания, которые в старую ширину не влезают — на PostgreSQL оно на них
    просто упадёт. Обратный ход оставлен ради полноты цепочки, а не как рабочий сценарий."""
    _retype_description(was=_NOW, now=_WAS)
