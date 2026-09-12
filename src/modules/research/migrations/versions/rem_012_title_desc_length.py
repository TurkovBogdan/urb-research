"""research: title 128 → 96, описание исследования 2048 → 512 — лишнее срезается

Заголовок и описание — строки для просмотра списка: по ним человек находит артефакт в реестре,
а агент выбирает, куда идти дальше, и обе он перечитывает целиком при каждом обзоре. Текст
артефакта живёт в ``body``, где лимита нет, поэтому широкое описание не давало ничего, кроме
токенов: 2048 у ``research_index`` были не замыслом, а слепком накопившихся данных (см.
``rem_009``). Теперь потолок один на четыре таблицы — 96 на заголовок, 512 на описание.

Данные, которые в новую ширину не влезли, **усекаются**: та же семантика, что у ``_clip`` в CRUD
модуля (``value[:limit]``), — иначе PostgreSQL просто отказался бы менять тип колонки. Строки,
которые и так влезают, не переписываются: условие по длине оставляет их нетронутыми и заодно
делает отчёт честным — в нём ровно те значения, у которых отрезан хвост.

``updated_at`` не упоминается ни одним из запросов: все четыре модели стамповали бы его
``onupdate=utc_now``, а реестр по нему сортирует и показывает как «когда тут работали». Запись
через ORM (или любой ``UPDATE`` с этой колонкой) сплющила бы историю реестра в момент миграции.

Усечение проходит по обеим колонкам всех четырёх таблиц, а не только там, где меняется
объявленная ширина: на SQLite ширина ничего не держит, и единственной границей до сих пор был
``_clip`` в CRUD — то есть длиннее 512 могло прилечь и в описание группы, области, заметки.
Ширина же меняется у четырёх заголовков и **одного** описания (``research_index``): у группы,
области и заметки колонка объявляла 512 и до этой ревизии.

Описание — одна из колонок, в которых ``rem_011`` переписывала ссылки на коды, поэтому рез по
512 в принципе способен разрубить код пополам и оставить ссылку в никуда. На сегодняшних данных
этого не случается (единственная ссылка среди усечённых описаний кончается за 8 символов до
реза), но искать границу ссылки усечение не умеет — такова цена того, что описание остаётся
строкой списка, а не текстом.

Сужение идёт **после** усечения и через ``batch_alter_table``: ALTER COLUMN на SQLite alembic не
умеет, там таблица пересобирается (проверку ссылок на время прогона снимает ``AlembicRunner``,
именованные ключ и CHECK переезжают через рефлексию), на PostgreSQL это обычный ALTER TYPE,
который на непоместившемся значении откажет (``value too long for type character varying(96)``).

Вне охвата: ``research_source_query`` / ``research_source_document`` (заголовков у них нет) и
``objective`` / ``scope`` / ``expectations`` области — это бриф раздела, а не строка списка.

Revision ID: rem_012_title_desc_length
Revises: rem_011_code_length
Create Date: 2026-09-12
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

revision: str = "rem_012_title_desc_length"
down_revision: Union[str, None] = "rem_011_code_length"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TITLE_MAX = 96
DESCRIPTION_MAX = 512
RETIRED_TITLE_MAX = 128
RETIRED_RESEARCH_DESCRIPTION_MAX = 2048

TABLES = ("research_index", "research_group", "research_area", "research_note")
CLIPPED_COLUMNS: dict[str, int] = {"title": TITLE_MAX, "description": DESCRIPTION_MAX}


def clip_overflowing_values(connection: Connection) -> Counter:
    """Фаза 1: хвосты длиннее нового потолка. Портируемый SQL — одинаково на SQLite и PostgreSQL."""
    clipped: Counter = Counter()
    for table in TABLES:
        for column, limit in CLIPPED_COLUMNS.items():
            overflowing = connection.execute(
                text(
                    f"UPDATE {table} SET {column} = substr({column}, 1, {limit})"
                    f" WHERE length({column}) > {limit}"
                )
            )
            if overflowing.rowcount:
                clipped[f"{table}.{column}"] = overflowing.rowcount
    return clipped


def narrow_titles() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "title",
                existing_type=sa.String(length=RETIRED_TITLE_MAX),
                type_=sa.String(length=TITLE_MAX),
                existing_nullable=False,
            )


def narrow_research_description() -> None:
    with op.batch_alter_table("research_index") as batch_op:
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=RETIRED_RESEARCH_DESCRIPTION_MAX),
            type_=sa.String(length=DESCRIPTION_MAX),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
        )


def print_report(clipped: Counter) -> None:
    print(f"{revision}: clipped {sum(clipped.values())} values")
    for column, count in sorted(clipped.items()):
        print(f"  {column}: {count}")


def upgrade() -> None:
    print_report(clip_overflowing_values(op.get_bind()))
    narrow_titles()
    narrow_research_description()


def downgrade() -> None:
    """Необратимо: отрезанные хвосты заголовков и описаний не хранятся нигде."""
    raise RuntimeError(f"{revision} is irreversible — the clipped tails are stored nowhere.")
