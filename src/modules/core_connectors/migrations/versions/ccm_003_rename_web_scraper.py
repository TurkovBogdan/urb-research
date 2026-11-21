"""core_connectors: код скрейпера web_scrapper → simple_web_scraper

Демон переименован (daemon-web-scrapper → simple-web-scraper), коннектор — вслед за ним.
Запись доступа хранит код коннектора строкой: без переименования она осиротела бы — реестр
больше не знает ``web_scrapper``, а новый код остался бы без подключения.

Revision ID: ccm_003_rename_web_scraper
Revises: ccm_002_access_title
Create Date: 2026-11-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ccm_003_rename_web_scraper"
down_revision: Union[str, None] = "ccm_002_access_title"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_CODE = "web_scrapper"
_NEW_CODE = "simple_web_scraper"


def upgrade() -> None:
    _rename(_OLD_CODE, _NEW_CODE)


def downgrade() -> None:
    _rename(_NEW_CODE, _OLD_CODE)


def _rename(old: str, new: str) -> None:
    access = sa.table("core_connectors_access", sa.column("connector", sa.String))
    op.execute(access.update().where(access.c.connector == old).values(connector=new))
