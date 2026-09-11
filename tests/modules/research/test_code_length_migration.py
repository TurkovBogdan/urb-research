"""Миграция ``rem_011_code_length``: коды research укорачиваются до 10 hex — ключи и тексты.

Ревизия импортируется файлом и зовётся своими же функциями, поэтому под тестом ровно тот код,
который выполнится на боевой базе (``heavy``-тесты идут только на PostgreSQL и без него молча
скипаются — на них тут не полагаемся). Фазы прогоняются так же, как их прогоняет
``AlembicRunner``: пишущая транзакция с выключенной проверкой ссылок, потому что фаза 1 переписывает
первичные ключи, на которые смотрят дети.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select, text

from src.core.database import get_engine, session_scope, write_scope
from src.core.database.sqlite import WRITE_EXECUTION_OPTIONS, foreign_keys_disabled
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery

_REVISION_FILE = (
    Path(__file__).resolve().parents[3]
    / "src/modules/research/migrations/versions/rem_011_code_length.py"
)


def _load_revision():
    """Ревизия как обычный модуль: alembic грузит её так же — по пути, вне пакета."""
    spec = importlib.util.spec_from_file_location(_REVISION_FILE.stem, _REVISION_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rem_011 = _load_revision()


def retired(head: str) -> str:
    """Код снятого формата: значащее начало + нули до 22 знаков."""
    return head.ljust(rem_011.RETIRED_CODE_LEN, "0")


RESEARCH = retired("aaaa11")
GROUP = retired("bbbb22")
AREA = retired("cccc33")
NOTE = retired("dddd44")
QUERY = retired("eeee55")
SOURCE = retired("ffff66")
DEAD_NOTE = retired("0000dead")
PAGE = retired("dead01")
SEARCH = retired("dead02")
BODY_HASH = "9f9f9f9f9f9f9f9f9f9f9f"

SEEDED_AT = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

RESEARCH_BODY = f"""# Обзор

Раздел AREA@{AREA} опирается на источник SOURCE@{SOURCE}.
Ссылка в никуда NOTE@{DEAD_NOTE} — код всё равно укорачивается.
Страница PAGE@{PAGE} и прогон SEARCH@{SEARCH} — коды другого модуля.
"""

AREA_BODY = f"""Точный дубль тела {SOURCE} — ссылка, написанная без префикса.

Хеш страницы {BODY_HASH} ссылкой не является.

```text
{BODY_HASH}
```
"""


def _live_codes() -> frozenset[str]:
    """Набор для чистых тестов: «живым» считается только укороченный код источника."""
    return frozenset({rem_011.shorten(SOURCE)})


# ── чистые: усечение и переписывание ссылок ──────────────────────────────────

@pytest.mark.pure
def test_shorten_cuts_to_the_new_length():
    assert rem_011.shorten(RESEARCH) == RESEARCH[: rem_011.CODE_LEN]
    assert len(rem_011.shorten(RESEARCH)) == rem_011.CODE_LEN


@pytest.mark.pure
def test_shorten_leaves_an_already_short_code_alone():
    short = rem_011.shorten(RESEARCH)

    assert rem_011.shorten(short) == short


@pytest.mark.pure
def test_typed_reference_is_shortened_even_when_it_resolves_to_nothing():
    text, produced = rem_011.shorten_references(f"см. NOTE@{DEAD_NOTE}.", frozenset())

    assert text == f"см. NOTE@{rem_011.shorten(DEAD_NOTE)}."
    assert produced == [rem_011.shorten(DEAD_NOTE)]


@pytest.mark.pure
def test_untyped_run_is_shortened_only_when_it_names_a_live_code():
    live, produced = rem_011.shorten_references(f"дубль {SOURCE} тут", _live_codes())
    foreign, untouched = rem_011.shorten_references(f"хеш {BODY_HASH} тут", _live_codes())

    assert live == f"дубль {rem_011.shorten(SOURCE)} тут"
    assert produced == [rem_011.shorten(SOURCE)]
    assert foreign == f"хеш {BODY_HASH} тут"
    assert untouched == []


@pytest.mark.pure
def test_web_search_references_keep_their_length():
    text, produced = rem_011.shorten_references(
        f"PAGE@{PAGE} и SEARCH@{SEARCH}", _live_codes()
    )

    assert text == f"PAGE@{PAGE} и SEARCH@{SEARCH}"
    assert produced == []


@pytest.mark.pure
def test_foreign_hex_in_a_fenced_block_survives():
    body = f"```text\n{BODY_HASH}\n```"

    assert rem_011.shorten_references(body, _live_codes())[0] == body


# ── db: фазы на засеянной базе ───────────────────────────────────────────────

def _run_phase(connection, work):
    connection.execution_options(**WRITE_EXECUTION_OPTIONS)
    with foreign_keys_disabled(connection):
        return work(connection)


async def _apply(work):
    """Прогнать фазу на боевом соединении — как это делает ``AlembicRunner._do_upgrade``."""
    async with get_engine().connect() as connection:
        return await connection.run_sync(_run_phase, work)


async def _convert():
    """Полный прогон ревизии: проверка на склейку → ключи → тексты."""

    def phases(connection):
        rem_011.raise_on_collisions(connection)
        rem_011.shorten_code_columns(connection)
        return rem_011.rewrite_text_columns(connection, rem_011.live_codes(connection))

    return await _apply(phases)


@pytest.fixture
async def seeded(db):
    """Шесть строк в снятом формате: ссылки на них живут и в ключах, и в текстах."""
    in_dependency_order = (
        ResearchGroup(code=GROUP, title="Группа", created_at=SEEDED_AT, updated_at=SEEDED_AT),
        Research(
            code=RESEARCH,
            group_code=GROUP,
            title="Исследование",
            body=RESEARCH_BODY,
            created_at=SEEDED_AT,
            updated_at=SEEDED_AT,
        ),
        ResearchArea(
            code=AREA,
            research_code=RESEARCH,
            title="Область",
            body=AREA_BODY,
            created_at=SEEDED_AT,
            updated_at=SEEDED_AT,
        ),
        ResearchNote(
            code=NOTE,
            research_code=RESEARCH,
            kind="result",
            title="Заметка",
            description=f"итог по AREA@{AREA}",
            created_at=SEEDED_AT,
            updated_at=SEEDED_AT,
        ),
        ResearchSourceQuery(
            code=QUERY,
            research_code=RESEARCH,
            area_code=AREA,
            search_code=SEARCH,
            query="как устроены коды",
            created_at=SEEDED_AT,
        ),
        ResearchSourceDocument(
            code=SOURCE,
            research_code=RESEARCH,
            area_code=AREA,
            query_code=QUERY,
            page_code=PAGE,
            status="kept",
            note=f"дубль QUERY@{QUERY}",
            created_at=SEEDED_AT,
            updated_at=SEEDED_AT,
        ),
    )
    async with write_scope() as s:
        for row in in_dependency_order:
            s.add(row)
            await s.flush()


_MODELS = (
    Research,
    ResearchGroup,
    ResearchArea,
    ResearchNote,
    ResearchSourceQuery,
    ResearchSourceDocument,
)


async def _rows(model):
    async with session_scope() as s:
        return (await s.execute(select(model))).scalars().all()


@pytest.mark.db
async def test_keys_and_their_references_shrink_together(seeded):
    await _convert()

    research = (await _rows(Research))[0]
    area = (await _rows(ResearchArea))[0]
    note = (await _rows(ResearchNote))[0]
    query = (await _rows(ResearchSourceQuery))[0]
    document = (await _rows(ResearchSourceDocument))[0]

    assert research.code == rem_011.shorten(RESEARCH)
    assert research.group_code == rem_011.shorten(GROUP)
    assert area.research_code == research.code
    assert note.research_code == research.code
    assert query.research_code == research.code
    assert query.area_code == area.code
    assert document.query_code == query.code
    assert document.area_code == area.code


@pytest.mark.db
async def test_web_search_soft_refs_keep_the_long_form(seeded):
    await _convert()

    query = (await _rows(ResearchSourceQuery))[0]
    document = (await _rows(ResearchSourceDocument))[0]

    assert query.search_code == SEARCH
    assert document.page_code == PAGE


@pytest.mark.db
async def test_text_references_follow_the_keys(seeded):
    await _convert()

    body = (await _rows(Research))[0].body
    area_body = (await _rows(ResearchArea))[0].body

    assert f"AREA@{rem_011.shorten(AREA)}" in body
    assert f"SOURCE@{rem_011.shorten(SOURCE)}" in body
    assert f"NOTE@{rem_011.shorten(DEAD_NOTE)}" in body
    assert f"PAGE@{PAGE}" in body
    assert f"SEARCH@{SEARCH}" in body
    assert f"дубль тела {rem_011.shorten(SOURCE)} —" in area_body
    assert BODY_HASH in area_body


@pytest.mark.db
async def test_no_retired_code_survives_in_text(seeded):
    await _convert()

    async with session_scope() as s:
        texts = [
            value
            for table, columns in rem_011.TEXT_COLUMNS.items()
            for row in (await s.execute(text(f"SELECT * FROM {table}"))).mappings()
            for column, value in row.items()
            if column in columns and value
        ]

    assert texts
    assert not [t for t in texts if rem_011._TYPED_REFERENCE.search(t)]


@pytest.mark.db
async def test_the_registry_keeps_its_order(seeded):
    """``updated_at`` — «когда тут работали»; миграция для реестра обязана быть невидимой."""
    stamped = [model for model in _MODELS if hasattr(model, "updated_at")]
    before = [row.updated_at for model in stamped for row in await _rows(model)]

    await _convert()

    assert [row.updated_at for model in stamped for row in await _rows(model)] == before


@pytest.mark.db
async def test_dead_reference_is_reported_with_its_location(seeded):
    rewrite = await _convert()

    assert [r for r in rewrite.dead_references if rem_011.shorten(DEAD_NOTE) in r]
    assert rewrite.replaced["research_index.body"] == 3


@pytest.mark.db
async def test_second_run_changes_nothing(seeded):
    await _convert()
    before = [(await _rows(Research))[0].body, (await _rows(ResearchArea))[0].body]

    rewrite = await _convert()

    assert rewrite.rows_touched == 0
    assert [(await _rows(Research))[0].body, (await _rows(ResearchArea))[0].body] == before


@pytest.mark.db
async def test_empty_base_converts_to_nothing(db):
    rewrite = await _convert()

    assert rewrite.rows_touched == 0
    assert rewrite.replaced == {}


@pytest.mark.heavy
async def test_phase_one_rewrites_a_parent_key_under_enforced_foreign_keys(db):
    """Ключи переписываются и там, где проверку ссылок никто не снимал, — то есть на PostgreSQL.

    По умолчанию набор идёт на in-memory SQLite, где ``AlembicRunner`` гасит проверку прагмой,
    и ветка ``foreign_keys_deferred`` не исполняется вовсе. Этот тест поэтому ``heavy``: без
    ``TEST_PG_DSN`` он скипается, а с ним работает на живой PostgreSQL — засев и прогон идут в
    транзакции, которая в конце откатывается, чтобы чужая база осталась нетронутой.
    """
    async with get_engine().connect() as connection:
        transaction = await connection.begin()
        try:
            adopted = await connection.run_sync(_shorten_a_seeded_parent)
        finally:
            await transaction.rollback()

    assert adopted == rem_011.shorten(RESEARCH)


def _shorten_a_seeded_parent(connection) -> str:
    # Колонка времени — без зоны (портируемый ``timestamp()``), а сырой SQL идёт мимо ORM,
    # которая обычно и снимает зону.
    seeded = {"research": RESEARCH, "area": AREA, "at": SEEDED_AT.replace(tzinfo=None)}
    connection.execute(
        text(
            "INSERT INTO research_index (code, title, created_at, updated_at)"
            " VALUES (:research, 'проба', :at, :at)"
        ),
        seeded,
    )
    connection.execute(
        text(
            "INSERT INTO research_area (code, research_code, title, created_at, updated_at)"
            " VALUES (:area, :research, 'проба', :at, :at)"
        ),
        seeded,
    )
    rem_011.shorten_code_columns(connection)
    return connection.execute(
        text("SELECT research_code FROM research_area WHERE code = :area"),
        {"area": rem_011.shorten(AREA)},
    ).scalar_one()


@pytest.mark.db
async def test_preflight_refuses_a_base_where_shortening_would_merge_codes(db):
    twin = RESEARCH[: rem_011.CODE_LEN] + "ffffffffffff"
    async with write_scope() as s:
        s.add_all(
            [
                Research(code=RESEARCH, title="Первое"),
                Research(code=twin, title="Второе"),
            ]
        )

    with pytest.raises(RuntimeError, match="research_index"):
        await _convert()

    assert {row.code for row in await _rows(Research)} == {RESEARCH, twin}
