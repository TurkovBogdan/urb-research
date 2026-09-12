"""Миграция ``rem_012_title_desc_length``: заголовок 96 и описание 512, лишнее срезается.

Ревизия импортируется файлом и зовётся своими же функциями, поэтому под тестом ровно тот код,
который выполнится на боевой базе. ``upgrade()`` идёт целиком: ``op`` подменяется живым
контекстом alembic на соединении прогона, так что ``batch_alter_table`` действительно
пересобирает таблицы — иначе порядок фаз (сначала усечение, потом сужение) не проверял бы никто.

Числа-потолки здесь записаны литералами, а не взяты из ревизии или из констант модуля: проверка,
которая делит константу с проверяемым, подтверждает лишь саму себя.

Прогон повторяет то, как ревизию исполняет ``AlembicRunner``: пишущая транзакция с выключенной
на время схемных работ проверкой ссылок.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select, text

from src.core.database import get_engine, session_scope, write_scope
from src.core.database.sqlite import WRITE_EXECUTION_OPTIONS, foreign_keys_disabled
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research

_REVISION_FILE = (
    Path(__file__).resolve().parents[3]
    / "src/modules/research/migrations/versions/rem_012_title_desc_length.py"
)


def _load_revision():
    """Ревизия как обычный модуль: alembic грузит её так же — по пути, вне пакета."""
    spec = importlib.util.spec_from_file_location(_REVISION_FILE.stem, _REVISION_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rem_012 = _load_revision()

TITLE_MAX = 96
DESCRIPTION_MAX = 512
RETIRED_TITLE_MAX = 128
RETIRED_RESEARCH_DESCRIPTION_MAX = 2048

TABLES = ("research_index", "research_group", "research_area", "research_note")

# Кириллица, а не латиница: усечение обязано резать по символам, а не по байтам.
OVERLONG_TITLE = "я" * 150
OVERLONG_DESCRIPTION = "ю" * 600
OVERLONG_OBJECTIVE = "э" * 600
FITTING_TITLE = "Влезает"
FITTING_DESCRIPTION = "Тоже влезает"

# Naive UTC — так хранит проект; tz-aware значение PostgreSQL в ``timestamp`` не примет.
SEEDED_AT = datetime(2026, 1, 2, 3, 4, 5)

_MODELS = (Research, ResearchGroup, ResearchArea, ResearchNote)

_NARROWED_SCHEMA = {
    "research_index.title": TITLE_MAX,
    "research_index.description": DESCRIPTION_MAX,
    "research_group.title": TITLE_MAX,
    "research_group.description": DESCRIPTION_MAX,
    "research_area.title": TITLE_MAX,
    "research_area.description": DESCRIPTION_MAX,
    "research_note.title": TITLE_MAX,
    "research_note.description": DESCRIPTION_MAX,
}

_PRE_MIGRATION_SCHEMA = {
    **_NARROWED_SCHEMA,
    "research_index.title": RETIRED_TITLE_MAX,
    "research_index.description": RETIRED_RESEARCH_DESCRIPTION_MAX,
    "research_group.title": RETIRED_TITLE_MAX,
    "research_area.title": RETIRED_TITLE_MAX,
    "research_note.title": RETIRED_TITLE_MAX,
}


def _operations(connection) -> Operations:
    """Живой контекст alembic на этом соединении — то, чем ``op`` является внутри ревизии."""
    return Operations(MigrationContext.configure(connection))


def _run_phase(connection, work):
    connection.execution_options(**WRITE_EXECUTION_OPTIONS)
    with foreign_keys_disabled(connection):
        return work(connection)


async def _apply(work):
    """Прогнать работу на боевом соединении — как это делает ``AlembicRunner._do_upgrade``.

    На SQLite транзакцию закрывает сама ``foreign_keys_disabled`` (прагму можно вернуть только
    вне неё); на PostgreSQL блок — no-op, и без явного ``commit`` закрытие соединения откатило бы
    всё сделанное.
    """
    async with get_engine().connect() as connection:
        result = await connection.run_sync(_run_phase, work)
        await connection.commit()
        return result


def _widen_to_the_pre_migration_schema(connection) -> None:
    """Ширины, которые миграция застаёт на боевой базе.

    Фикстура ``db`` строит схему по сегодняшним моделям, то есть уже суженную, — и тест стартовал
    бы из состояния, которого до ревизии не бывает: на SQLite длинное значение туда влезает
    молча, на PostgreSQL его не засеять вовсе.
    """
    operations = _operations(connection)
    for table in TABLES:
        with operations.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "title",
                existing_type=sa.String(length=TITLE_MAX),
                type_=sa.String(length=RETIRED_TITLE_MAX),
                existing_nullable=False,
            )
    with operations.batch_alter_table("research_index") as batch_op:
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=DESCRIPTION_MAX),
            type_=sa.String(length=RETIRED_RESEARCH_DESCRIPTION_MAX),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
        )


def _upgrade_entry_point(monkeypatch):
    """``upgrade()`` как её зовёт alembic: ``op`` привязан к соединению прогона."""

    def run(connection):
        monkeypatch.setattr(rem_012, "op", _operations(connection))
        rem_012.upgrade()

    return run


def _column_widths(connection) -> dict[str, int]:
    inspector = sa.inspect(connection)
    return {
        f"{table}.{column['name']}": column["type"].length
        for table in TABLES
        for column in inspector.get_columns(table)
        if column["name"] in ("title", "description")
    }


def _longest_values(connection) -> dict[str, int]:
    """Самое длинное значение каждой колонки по всем четырём таблицам."""
    return {
        column: max(
            connection.execute(
                text(f"SELECT coalesce(max(length({column})), 0) FROM {table}")
            ).scalar_one()
            for table in TABLES
        )
        for column in ("title", "description")
    }


async def _clip():
    return await _apply(rem_012.clip_overflowing_values)


async def _rows(model):
    async with session_scope() as s:
        return (await s.execute(select(model).order_by(model.code))).scalars().all()


@pytest.fixture
async def seeded(db):
    """Схема до ревизии плюс по две строки в каждой таблице: одна не влезает, вторая влезает."""
    await _apply(_widen_to_the_pre_migration_schema)
    in_dependency_order = (
        ResearchGroup(code="group00001", title=OVERLONG_TITLE, description=OVERLONG_DESCRIPTION),
        ResearchGroup(code="group00002", title=FITTING_TITLE, description=FITTING_DESCRIPTION),
        Research(code="resear0001", title=OVERLONG_TITLE, description=OVERLONG_DESCRIPTION),
        Research(code="resear0002", title=FITTING_TITLE, description=FITTING_DESCRIPTION),
        ResearchArea(
            code="area000001",
            research_code="resear0001",
            title=OVERLONG_TITLE,
            description=OVERLONG_DESCRIPTION,
            objective=OVERLONG_OBJECTIVE,
        ),
        ResearchArea(
            code="area000002",
            research_code="resear0001",
            title=FITTING_TITLE,
            description=FITTING_DESCRIPTION,
        ),
        ResearchNote(
            code="note000001",
            research_code="resear0001",
            kind="result",
            title=OVERLONG_TITLE,
            description=OVERLONG_DESCRIPTION,
        ),
        ResearchNote(
            code="note000002",
            research_code="resear0001",
            kind="result",
            title=FITTING_TITLE,
            description=FITTING_DESCRIPTION,
        ),
    )
    async with write_scope() as s:
        for row in in_dependency_order:
            row.created_at = SEEDED_AT
            row.updated_at = SEEDED_AT
            s.add(row)
            await s.flush()


@pytest.mark.pure
def test_downgrade_refuses_because_the_clipped_tails_are_stored_nowhere():
    with pytest.raises(RuntimeError, match="irreversible"):
        rem_012.downgrade()


@pytest.mark.db
async def test_the_fixture_starts_from_the_width_the_migration_meets(seeded):
    assert await _apply(_column_widths) == _PRE_MIGRATION_SCHEMA


@pytest.mark.db
async def test_upgrade_clips_the_values_and_narrows_the_columns(seeded, monkeypatch, capsys):
    await _apply(_upgrade_entry_point(monkeypatch))

    clipped = [(await _rows(model))[0] for model in _MODELS]

    assert [row.title for row in clipped] == ["я" * TITLE_MAX] * len(_MODELS)
    assert [row.description for row in clipped] == ["ю" * DESCRIPTION_MAX] * len(_MODELS)
    assert await _apply(_column_widths) == _NARROWED_SCHEMA
    assert f"{rem_012.revision}: clipped 8 values" in capsys.readouterr().out


@pytest.mark.db
async def test_columns_are_narrowed_only_after_every_value_fits(seeded, monkeypatch):
    """Порядок фаз — не деталь оформления: сужение колонки, в которой лежит длинное значение,
    PostgreSQL отвергает (``value too long for type character varying(96)``), а SQLite проглотит
    молча. Поэтому перестановку ловит не провайдер, а замер в момент сужения."""
    narrow_titles = rem_012.narrow_titles
    longest_when_narrowing = []

    def measure_then_narrow() -> None:
        longest_when_narrowing.append(_longest_values(rem_012.op.get_bind()))
        narrow_titles()

    monkeypatch.setattr(rem_012, "narrow_titles", measure_then_narrow)

    await _apply(_upgrade_entry_point(monkeypatch))

    assert longest_when_narrowing == [{"title": TITLE_MAX, "description": DESCRIPTION_MAX}]


@pytest.mark.db
async def test_overlong_values_are_cut_to_the_new_ceiling(seeded):
    await _clip()

    clipped = [(await _rows(model))[0] for model in _MODELS]

    assert [row.title for row in clipped] == ["я" * TITLE_MAX] * len(_MODELS)
    assert [row.description for row in clipped] == ["ю" * DESCRIPTION_MAX] * len(_MODELS)


@pytest.mark.db
async def test_values_that_already_fit_are_left_alone(seeded):
    await _clip()

    fitting = [(await _rows(model))[1] for model in _MODELS]

    assert [row.title for row in fitting] == [FITTING_TITLE] * len(_MODELS)
    assert [row.description for row in fitting] == [FITTING_DESCRIPTION] * len(_MODELS)


@pytest.mark.db
async def test_the_area_brief_keeps_its_own_width(seeded):
    """``objective`` / ``scope`` / ``expectations`` — бриф раздела, а не строка списка: не наш охват."""
    await _clip()

    assert (await _rows(ResearchArea))[0].objective == OVERLONG_OBJECTIVE


@pytest.mark.db
async def test_the_registry_keeps_its_order(seeded, monkeypatch):
    """``updated_at`` — «когда тут работали»; миграция для реестра обязана быть невидимой."""
    before = [row.updated_at for model in _MODELS for row in await _rows(model)]

    await _apply(_upgrade_entry_point(monkeypatch))

    assert [row.updated_at for model in _MODELS for row in await _rows(model)] == before


@pytest.mark.db
async def test_second_run_clips_nothing(seeded):
    await _clip()
    before = [row.title for model in _MODELS for row in await _rows(model)]

    assert await _clip() == {}
    assert [row.title for model in _MODELS for row in await _rows(model)] == before


@pytest.mark.db
async def test_empty_base_clips_nothing(db):
    assert await _clip() == {}


@pytest.mark.db
async def test_report_lists_every_column_with_its_count(seeded, capsys):
    rem_012.print_report(await _clip())

    report = capsys.readouterr().out.splitlines()

    assert report[0] == f"{rem_012.revision}: clipped 8 values"
    assert report[1:] == [
        "  research_area.description: 1",
        "  research_area.title: 1",
        "  research_group.description: 1",
        "  research_group.title: 1",
        "  research_index.description: 1",
        "  research_index.title: 1",
        "  research_note.description: 1",
        "  research_note.title: 1",
    ]
