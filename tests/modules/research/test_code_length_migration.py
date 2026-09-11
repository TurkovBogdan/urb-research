"""Миграция ``rem_011_code_length``: коды research укорачиваются до 10 hex — ключи и тексты.

Ревизия импортируется файлом и зовётся своими же функциями, поэтому под тестом ровно тот код,
который выполнится на боевой базе (``heavy``-тесты идут только на PostgreSQL и без него молча
скипаются — на них тут не полагаемся). Фазы прогоняются так же, как их прогоняет
``AlembicRunner``: пишущая транзакция с выключенной проверкой ссылок, потому что фаза 1 переписывает
первичные ключи, на которые смотрят дети.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

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

# Naive UTC — так хранит проект; tz-aware значение PostgreSQL в ``timestamp`` не примет.
SEEDED_AT = datetime(2026, 1, 2, 3, 4, 5)

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


@pytest.mark.pure
def test_downgrade_refuses_because_the_discarded_tail_is_stored_nowhere():
    with pytest.raises(RuntimeError, match="irreversible"):
        rem_011.downgrade()


# ── db: фазы на засеянной базе ───────────────────────────────────────────────

def _run_phase(connection, work):
    connection.execution_options(**WRITE_EXECUTION_OPTIONS)
    with foreign_keys_disabled(connection):
        return work(connection)


async def _apply(work):
    """Прогнать фазу на боевом соединении — как это делает ``AlembicRunner._do_upgrade``.

    На SQLite транзакцию закрывает сама ``foreign_keys_disabled`` (прагму можно вернуть только
    вне неё); на PostgreSQL блок — no-op, и без явного ``commit`` закрытие соединения откатило бы
    всё сделанное.
    """
    async with get_engine().connect() as connection:
        result = await connection.run_sync(_run_phase, work)
        await connection.commit()
        return result


def _upgrade_entry_point(monkeypatch):
    """``upgrade()`` как её зовёт alembic: ``op.get_bind()`` отдаёт соединение прогона."""

    def run(connection):
        monkeypatch.setattr(rem_011, "op", SimpleNamespace(get_bind=lambda: connection))
        rem_011.upgrade()

    return run


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


@pytest.mark.db
async def test_report_lists_columns_counts_and_dead_references(seeded, capsys):
    rem_011.print_report(await _convert())

    report = capsys.readouterr().out.splitlines()

    assert report[0] == f"{rem_011.revision}: rewrote 4 rows"
    assert "  research_index.body: 3" in report
    assert "  research_area.body: 1" in report
    assert "  research_note.description: 1" in report
    assert "  research_source_document.note: 1" in report
    assert f"{rem_011.revision}: references resolving to nothing (1):" in report
    assert (
        f"  research_index.body {rem_011.shorten(RESEARCH)}: {rem_011.shorten(DEAD_NOTE)}"
        in report
    )


@pytest.mark.db
async def test_collisions_come_back_per_table_with_every_code_involved(db):
    twin = RESEARCH[: rem_011.CODE_LEN] + "ffffffffffff"
    async with write_scope() as s:
        s.add_all(
            [
                Research(code=RESEARCH, title="Первое"),
                Research(code=twin, title="Второе"),
                ResearchGroup(code=GROUP, title="Одна, без пары"),
            ]
        )

    collisions = await _apply(rem_011.colliding_codes)

    assert collisions == {"research_index": sorted([RESEARCH, twin])}


@pytest.mark.db
async def test_a_base_without_collisions_reports_none(seeded):
    assert await _apply(rem_011.colliding_codes) == {}


@pytest.mark.db
async def test_upgrade_entry_point_runs_every_phase_and_prints_the_report(
    seeded, monkeypatch, capsys
):
    await _apply(_upgrade_entry_point(monkeypatch))

    research = (await _rows(Research))[0]
    document = (await _rows(ResearchSourceDocument))[0]
    assert research.code == rem_011.shorten(RESEARCH)
    assert f"AREA@{rem_011.shorten(AREA)}" in research.body
    assert document.query_code == rem_011.shorten(QUERY)
    assert document.page_code == PAGE
    assert f"{rem_011.revision}: rewrote 4 rows" in capsys.readouterr().out


@pytest.mark.db
async def test_upgrade_entry_point_stops_at_the_preflight(db, monkeypatch):
    twin = RESEARCH[: rem_011.CODE_LEN] + "ffffffffffff"
    async with write_scope() as s:
        s.add_all([Research(code=RESEARCH, title="Первое"), Research(code=twin, title="Второе")])

    with pytest.raises(RuntimeError, match="research_index"):
        await _apply(_upgrade_entry_point(monkeypatch))

    assert {row.code for row in await _rows(Research)} == {RESEARCH, twin}


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


def _seed_a_parent_and_its_child(connection) -> dict[str, object]:
    seeded = {"research": RESEARCH, "area": AREA, "at": SEEDED_AT}
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
    return seeded


def _shorten_a_seeded_parent(connection) -> str:
    _seed_a_parent_and_its_child(connection)
    rem_011.shorten_code_columns(connection)
    return connection.execute(
        text("SELECT research_code FROM research_area WHERE code = :area"),
        {"area": rem_011.shorten(AREA)},
    ).scalar_one()


def _deferrable_research_foreign_keys(connection) -> int:
    """Сколько ключей, смотрящих на таблицы research, объявлены ``DEFERRABLE`` прямо сейчас."""
    parents = ", ".join(f"'{table}'" for table in rem_011.CODE_COLUMNS)
    return connection.execute(
        text(
            "SELECT count(*) FROM pg_constraint AS c"
            " JOIN pg_class AS parent ON parent.oid = c.confrelid"
            f" WHERE c.contype = 'f' AND c.condeferrable AND parent.relname IN ({parents})"
        )
    ).scalar_one()


def _rewrite_both_sides_inside_the_deferred_block(connection) -> tuple[int, int]:
    """(ключей отложено внутри блока, ключей отложено после него) при согласованной фазе."""
    seeded = _seed_a_parent_and_its_child(connection)
    moved = {**seeded, "moved": rem_011.shorten(RESEARCH)}
    with rem_011.foreign_keys_deferred(connection):
        deferred_inside = _deferrable_research_foreign_keys(connection)
        connection.execute(
            text("UPDATE research_index SET code = :moved WHERE code = :research"), moved
        )
        connection.execute(
            text("UPDATE research_area SET research_code = :moved WHERE code = :area"), moved
        )
    return deferred_inside, _deferrable_research_foreign_keys(connection)


def _orphan_the_child_inside_the_deferred_block(connection) -> None:
    seeded = _seed_a_parent_and_its_child(connection)
    with rem_011.foreign_keys_deferred(connection):
        connection.execute(
            text("UPDATE research_index SET code = :moved WHERE code = :research"),
            {**seeded, "moved": rem_011.shorten(RESEARCH)},
        )


@pytest.mark.heavy
async def test_deferral_is_lifted_at_the_end_of_a_consistent_phase(db):
    """Внутри блока ключи отложены, после него — снова ``NOT DEFERRABLE``, ещё до коммита:
    восстановление делает сам блок, а не откат транзакции."""
    async with get_engine().connect() as connection:
        transaction = await connection.begin()
        try:
            deferred_inside, deferred_after = await connection.run_sync(
                _rewrite_both_sides_inside_the_deferred_block
            )
        finally:
            await transaction.rollback()

    assert deferred_inside > 0
    assert deferred_after == 0


@pytest.mark.heavy
async def test_an_orphan_left_inside_the_block_is_refused_when_the_deferral_ends(db):
    """Отложить — не значит снять: ``SET CONSTRAINTS ALL IMMEDIATE`` в конце блока ловит
    висящего ребёнка, транзакция откатывается, и ни один ключ не остаётся ``DEFERRABLE``."""
    async with get_engine().connect() as connection:
        transaction = await connection.begin()
        try:
            with pytest.raises(IntegrityError, match="research_area"):
                await connection.run_sync(_orphan_the_child_inside_the_deferred_block)
        finally:
            await transaction.rollback()

    async with get_engine().connect() as connection:
        assert await connection.run_sync(_deferrable_research_foreign_keys) == 0


@pytest.mark.heavy
async def test_upgrade_entry_point_runs_under_enforced_foreign_keys(seeded, monkeypatch, capsys):
    """Весь ``upgrade()`` на PostgreSQL: фаза 1 идёт через отложенные ключи на засеянных
    связанных строках, фаза 2 переписывает тексты, отчёт печатается."""
    await _apply(_upgrade_entry_point(monkeypatch))

    area = (await _rows(ResearchArea))[0]
    query = (await _rows(ResearchSourceQuery))[0]
    assert area.research_code == rem_011.shorten(RESEARCH)
    assert query.area_code == rem_011.shorten(AREA)
    assert query.search_code == SEARCH
    assert f"{rem_011.revision}: rewrote 4 rows" in capsys.readouterr().out


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
