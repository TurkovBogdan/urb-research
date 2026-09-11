"""web_search: индекс на web_search_query_result.page_code

Вторая колонка внешнего ключа таблицы результатов осталась без индекса — индексирован был
только ``query_code``. Удаление страницы ищет свои результаты именно по ``page_code``, и без
индекса этот поиск идёт сканом по всей таблице результатов.

Revision ID: wsm_004_result_page_index
Revises: wsm_003_result
Create Date: 2026-09-06
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "wsm_004_result_page_index"
down_revision: Union[str, None] = "wsm_003_result"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "web_search_query_result"
_INDEX = "ix_web_search_query_result_page_code"


def upgrade() -> None:
    op.create_index(_INDEX, _TABLE, ["page_code"])


def downgrade() -> None:
    op.drop_index(_INDEX, table_name=_TABLE)
