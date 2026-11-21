"""web_search: web_search_page.fetch_access_id

Страница запоминает подключение, через которое её тянули: у коннектора их бывает несколько
(скрейпер напрямую и через VPN), и одного кода движка мало, чтобы понять, каким путём
прошла страница. Внешнего ключа нет: запись подключения принадлежит другому модулю и может
быть удалена, а след попытки должен остаться.

Revision ID: wsm_006_page_fetch_access
Revises: wsm_005_rename_web_scraper
Create Date: 2026-11-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "wsm_006_page_fetch_access"
down_revision: Union[str, None] = "wsm_005_rename_web_scraper"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "web_search_page"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("fetch_access_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.drop_column("fetch_access_id")
