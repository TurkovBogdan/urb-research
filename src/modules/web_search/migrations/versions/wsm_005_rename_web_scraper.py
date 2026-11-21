"""web_search: код движка контента web_scrapper → simple_web_scraper

Движок переименован вслед за демоном (daemon-web-scrapper → simple-web-scraper). Код лежит
строкой в истории прогонов и страниц и в настройке ``fetch_engine``: без переименования
настройка указывала бы на движок, которого в реестре больше нет, а история — на чужое имя.

Настройка живёт в таблице ядра, отсюда ``depends_on`` на ревизию, которая её создаёт: порядок
между цепочками иначе не задан, и на пустой базе обновление могло бы прийти раньше таблицы.

Revision ID: wsm_005_rename_web_scraper
Revises: wsm_004_result_page_index
Create Date: 2026-11-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "wsm_005_rename_web_scraper"
down_revision: Union[str, None] = "wsm_004_result_page_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = "com_004_modules_settings"

_OLD_CODE = "web_scrapper"
_NEW_CODE = "simple_web_scraper"


def upgrade() -> None:
    _rename(_OLD_CODE, _NEW_CODE)


def downgrade() -> None:
    _rename(_NEW_CODE, _OLD_CODE)


def _rename(old: str, new: str) -> None:
    for table_name in ("web_search_query", "web_search_page"):
        table = sa.table(table_name, sa.column("fetch_engine", sa.String))
        op.execute(table.update().where(table.c.fetch_engine == old).values(fetch_engine=new))

    settings = sa.table(
        "core_modules_settings",
        sa.column("module", sa.String),
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
    )
    op.execute(
        settings.update()
        .where(
            settings.c.module == "web_search",
            settings.c.key == "fetch_engine",
            settings.c.value == old,
        )
        .values(value=new)
    )
