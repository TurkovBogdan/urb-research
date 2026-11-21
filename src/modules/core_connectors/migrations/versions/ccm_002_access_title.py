"""core_connectors: core_connectors_access.title

Название подключения вернулось вместе со списком подключений: у коннектора бывает несколько
записей (два экземпляра скрейпера — напрямую и через VPN), и в списке их надо различать.
``null`` — подключение без названия.

Revision ID: ccm_002_access_title
Revises: ccm_001_access
Create Date: 2026-11-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ccm_002_access_title"
down_revision: Union[str, None] = "ccm_001_access"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "core_connectors_access"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("title", sa.String(length=96), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.drop_column("title")
