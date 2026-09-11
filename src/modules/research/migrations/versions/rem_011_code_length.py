"""research: entity codes shrink to a 10-hex tail — keys, foreign keys and the text citing them

A research code is what the agent retypes into every body, and it pays for it in tokens: the
22-hex tail becomes 10 (``RESEARCH@279d8a77f1``), which is ~6.8 tokens per citation. Measured on
the live base, truncating to 10 produces no collision in any code table, and none of the six
research codes carries dedup meaning — a collision would fail an insert, never merge two rows.

**New code = the old code truncated to its first 10 characters.** The mapping is computable
rather than stored, and that single property carries the whole conversion: each phase derives
the new value from the old one alone, so the pass is idempotent (nothing matches the long form
afterwards), order-free (rows are independent) and the text rewrite is one prefix-anchored
regex. One revision holds all three phases because ``alembic_version`` then answers "has this
run" and the revision's own transaction answers "did it finish".

Anchored on the **type prefix**, never on "any 22 hex": the corpus is full of foreign hex (page
body hashes, UUID fragments). The one exception is a bare run that truncates onto a live code —
a real cross-reference an agent wrote without its prefix — and checking against the live set is
what makes rewriting it safe. A hex run right after ``@`` is never touched: that is a typed
reference into web_search (``SEARCH@`` / ``PAGE@``), whose codes keep their length.

Out of scope, deliberately: ``web_search`` codes, and therefore the soft refs pointing at them
(``research_source_query.search_code`` / ``research_source_document.page_code``). They are never
shown to the agent, so shortening them would save zero tokens while making page dedup collide on
a 40-bit hash.

Foreign keys are handled per provider, because only one of them is already covered:
``AlembicRunner`` suspends the check on SQLite (a connection pragma) but does nothing on
PostgreSQL, where rewriting a parent key would be refused row by row. Phase 1 therefore opens
``foreign_keys_deferred`` — a no-op on SQLite, and on PostgreSQL a deferral to the end of the
phase, so the check still happens inside the migration's transaction.

``updated_at`` must not move: five of the six models stamp it ``onupdate=utc_now`` and the
registry sorts by it, so phase 2 writes raw SQL that never mentions the column. Writing through
the ORM would flatten the whole registry's history into this migration's timestamp.

Every literal here — the prefix words, both lengths, the column lists — is frozen on purpose: a
revision is a snapshot of intent and replays years later against module code that has moved on.

Revision ID: rem_011_code_length
Revises: rem_010_source_doc_fk_indexes
Create Date: 2026-09-11
"""

from __future__ import annotations

import re
from collections import Counter
from contextlib import contextmanager
from typing import Iterator, Sequence, Union

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

revision: str = "rem_011_code_length"
down_revision: Union[str, None] = "rem_010_source_doc_fk_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CODE_LEN = 10
RETIRED_CODE_LEN = 22
CODE_PREFIXES = ("RESEARCH", "AREA", "NOTE", "QUERY", "SOURCE", "GROUP")

CODE_COLUMNS: dict[str, tuple[str, ...]] = {
    "research_index": ("code", "group_code"),
    "research_group": ("code",),
    "research_area": ("code", "research_code"),
    "research_note": ("code", "research_code"),
    "research_source_query": ("code", "research_code", "area_code"),
    "research_source_document": ("code", "research_code", "area_code", "query_code"),
}

# Каждая текстовая колонка шести таблиц, а не сегодняшний список попаданий: в
# ``research_area.expectations`` ссылок нет только потому, что туда ещё не писали.
TEXT_COLUMNS: dict[str, tuple[str, ...]] = {
    "research_index": ("title", "description", "body"),
    "research_group": ("title", "description"),
    "research_area": ("title", "description", "objective", "scope", "expectations", "body"),
    "research_note": ("title", "description", "body"),
    "research_source_query": ("query",),
    "research_source_document": ("summary", "note"),
}

_TYPED_REFERENCE = re.compile(
    rf"\b(?P<word>{'|'.join(CODE_PREFIXES)})@(?P<tail>[0-9a-f]{{{RETIRED_CODE_LEN}}})(?![0-9a-f])"
)
# Слева запрещена и ``@``: хвост после неё — типизированная ссылка (``SEARCH@`` / ``PAGE@``),
# то есть код web_search, который эта миграция не трогает.
_UNTYPED_RUN = re.compile(rf"(?<![0-9a-f@])[0-9a-f]{{{RETIRED_CODE_LEN}}}(?![0-9a-f])")


def shorten(code: str) -> str:
    """Новый код из старого. Уже короткий возвращается собой — отсюда идемпотентность прогона."""
    return code[:CODE_LEN]


def shorten_references(value: str, live_codes: frozenset[str]) -> tuple[str, list[str]]:
    """Текст с укороченными ссылками + коды, которые в нём получились.

    Типизированная ссылка укорачивается всегда; голый прогон hex — только если укорачивается
    ровно в существующий код (иначе это чужой хеш, а не ссылка).
    """
    produced: list[str] = []

    def shorten_typed(match: re.Match[str]) -> str:
        code = shorten(match.group("tail"))
        produced.append(code)
        return f"{match.group('word')}@{code}"

    def shorten_untyped(match: re.Match[str]) -> str:
        code = shorten(match.group(0))
        if code not in live_codes:
            return match.group(0)
        produced.append(code)
        return code

    typed_shortened = _TYPED_REFERENCE.sub(shorten_typed, value)
    return _UNTYPED_RUN.sub(shorten_untyped, typed_shortened), produced


def colliding_codes(connection: Connection) -> dict[str, list[str]]:
    """Таблица → её коды, которые после усечения перестали бы различаться."""
    collisions: dict[str, list[str]] = {}
    for table in CODE_COLUMNS:
        codes = connection.execute(text(f"SELECT code FROM {table}")).scalars().all()
        occurrences = Counter(shorten(code) for code in codes)
        clashing = sorted(code for code in codes if occurrences[shorten(code)] > 1)
        if clashing:
            collisions[table] = clashing
    return collisions


def raise_on_collisions(connection: Connection) -> None:
    """Проверка до первой записи: усечение обязано остаться обратимым на этой базе."""
    collisions = colliding_codes(connection)
    if collisions:
        raise RuntimeError(
            f"{revision}: усечение до {CODE_LEN} знаков склеило бы разные коды — {collisions}"
        )


_IMMEDIATE_FOREIGN_KEYS = f"""
    SELECT child.relname AS child_table, constraint_.conname AS constraint_name
      FROM pg_constraint AS constraint_
      JOIN pg_class AS child ON child.oid = constraint_.conrelid
      JOIN pg_class AS parent ON parent.oid = constraint_.confrelid
     WHERE constraint_.contype = 'f'
       AND NOT constraint_.condeferrable
       AND parent.relname IN ({", ".join(f"'{table}'" for table in CODE_COLUMNS)})
"""


@contextmanager
def foreign_keys_deferred(connection: Connection) -> Iterator[None]:
    """Отложить проверку ссылок до конца блока — иначе фазу 1 нельзя выполнить в принципе.

    Переписывание первичного ключа на мгновение оставляет детей висящими, и PostgreSQL валит
    первый же ``UPDATE`` родителя (``ON UPDATE CASCADE`` у ключей нет). Проверка откладывается,
    а не снимается: в конце блока ``SET CONSTRAINTS ALL IMMEDIATE`` требует её немедленно, всё
    ещё внутри транзакции миграции, — то есть рассогласование поймается и откатится.

    Откладывать умеет только тот ключ, что объявлен ``DEFERRABLE``, поэтому имена ключей ищутся
    в каталоге (в моделях они безымянные, имена придумывает сама база) и после прогона
    возвращаются в исходное ``NOT DEFERRABLE``. На SQLite блок ничего не делает: там проверку
    уже сняла прагма на соединении (``AlembicRunner._do_upgrade``).
    """
    if connection.dialect.name != "postgresql":
        yield
        return
    constraints = connection.execute(text(_IMMEDIATE_FOREIGN_KEYS)).all()
    for child_table, constraint_name in constraints:
        connection.execute(
            text(
                f'ALTER TABLE {child_table} '
                f'ALTER CONSTRAINT "{constraint_name}" DEFERRABLE INITIALLY DEFERRED'
            )
        )
    connection.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    yield
    connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    for child_table, constraint_name in constraints:
        connection.execute(
            text(f'ALTER TABLE {child_table} ALTER CONSTRAINT "{constraint_name}" NOT DEFERRABLE')
        )


def shorten_code_columns(connection: Connection) -> None:
    """Фаза 1: ключи и ссылки на них. Портируемый SQL — одинаково на SQLite и PostgreSQL."""
    with foreign_keys_deferred(connection):
        for table, columns in CODE_COLUMNS.items():
            for column in columns:
                connection.execute(
                    text(f"UPDATE {table} SET {column} = substr({column}, 1, {CODE_LEN})")
                )


def live_codes(connection: Connection) -> frozenset[str]:
    """Коды всех шести таблиц — по ним ссылка в тексте считается живой."""
    return frozenset(
        code
        for table in CODE_COLUMNS
        for code in connection.execute(text(f"SELECT code FROM {table}")).scalars()
    )


class TextRewrite:
    """Итог фазы 2: сколько ссылок переписано по колонкам и какие из них никуда не ведут.

    Обычный класс, а не ``dataclass``: alembic исполняет файл ревизии, не регистрируя его в
    ``sys.modules``, а ``dataclass`` при разборе аннотаций лезет туда за модулем класса.
    """

    def __init__(self) -> None:
        self.rows_touched = 0
        self.replaced: Counter = Counter()
        self.dead_references: list[str] = []


def rewrite_text_columns(connection: Connection, codes: frozenset[str]) -> TextRewrite:
    """Фаза 2: ссылки внутри текстов. Единица работы — строка, ``updated_at`` не упоминается."""
    rewrite = TextRewrite()
    for table, columns in TEXT_COLUMNS.items():
        selected = ", ".join(("code", *columns))
        rows = connection.execute(text(f"SELECT {selected} FROM {table}")).mappings().all()
        for row in rows:
            changed: dict[str, str] = {}
            for column in columns:
                value = row[column]
                if not value:
                    continue
                shortened, produced = shorten_references(value, codes)
                if shortened == value:
                    continue
                changed[column] = shortened
                rewrite.replaced[f"{table}.{column}"] += len(produced)
                rewrite.dead_references.extend(
                    f"{table}.{column} {row['code']}: {code}"
                    for code in produced
                    if code not in codes
                )
            if not changed:
                continue
            assignments = ", ".join(f"{column} = :{column}" for column in changed)
            connection.execute(
                text(f"UPDATE {table} SET {assignments} WHERE code = :row_code"),
                {**changed, "row_code": row["code"]},
            )
            rewrite.rows_touched += 1
    return rewrite


def print_report(rewrite: TextRewrite) -> None:
    """Фаза 3: что переписано и какие ссылки не разрешились (они были мертвы и до миграции)."""
    print(f"{revision}: rewrote {rewrite.rows_touched} rows")
    for column, count in sorted(rewrite.replaced.items()):
        print(f"  {column}: {count}")
    print(f"{revision}: references resolving to nothing ({len(rewrite.dead_references)}):")
    for reference in rewrite.dead_references:
        print(f"  {reference}")


def upgrade() -> None:
    connection = op.get_bind()
    raise_on_collisions(connection)
    shorten_code_columns(connection)
    print_report(rewrite_text_columns(connection, live_codes(connection)))


def downgrade() -> None:
    """Необратимо: отброшенный хвост кода не хранится нигде, восстанавливать не из чего."""
    raise RuntimeError(f"{revision} is irreversible — the discarded code tail is stored nowhere.")
