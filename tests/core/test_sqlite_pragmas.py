"""Настройки SQLite: состав прагм, их применение на каждом соединении и внешние ключи."""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from sqlalchemy import event, exc, insert, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import Config
from src.core.database.runtime import create_all
from src.core.database.sqlite import (
    WRITE_EXECUTION_OPTIONS,
    configure_sqlite,
    connection_pragmas,
    foreign_keys_disabled,
    foreign_keys_enabled,
)
from src.core.models.tasks import CoreTask, CoreTaskLog, CoreTaskLogLevel, CoreTaskStatus
from src.core.utils.date import utc_now


def _file_config(path) -> Config:
    return Config(db_provider="sqlite", db_path=str(path))


async def _read_pragma(engine, name: str):
    async with engine.connect() as conn:
        return (await conn.execute(text(f"PRAGMA {name}"))).scalar()


@pytest.mark.pure
def test_postgres_gets_no_pragmas():
    assert connection_pragmas(Config(db_provider="postgres", db_host="h", db_name="n",
                                     db_user="u", db_password="p", db_ssl=False)) == ()


@pytest.mark.pure
def test_in_memory_skips_journal_mode():
    pragmas = connection_pragmas(Config(db_provider="sqlite", db_path=":memory:"))
    assert not any("journal_mode" in statement for statement in pragmas)
    assert "PRAGMA synchronous = NORMAL" in pragmas


@pytest.mark.pure
def test_file_database_asks_for_wal_first():
    pragmas = connection_pragmas(Config(db_provider="sqlite", db_path="/tmp/x.sqlite3"))
    assert pragmas[0] == "PRAGMA journal_mode = WAL"


@pytest.mark.db
async def test_file_database_connection_is_tuned(tmp_path):
    config = _file_config(tmp_path / "app.sqlite3")
    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    configure_sqlite(engine, config)
    try:
        assert await _read_pragma(engine, "journal_mode") == "wal"
        assert await _read_pragma(engine, "synchronous") == 1
        assert await _read_pragma(engine, "journal_size_limit") == 67108864
    finally:
        await engine.dispose()


@pytest.mark.db
async def test_settings_survive_a_fresh_connection(tmp_path):
    """Прагмы соединения сбрасываются при переподключении — слушатель ставит их заново."""
    config = _file_config(tmp_path / "app.sqlite3")
    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    configure_sqlite(engine, config)
    try:
        assert await _read_pragma(engine, "synchronous") == 1
        await engine.dispose()
        assert await _read_pragma(engine, "synchronous") == 1
    finally:
        await engine.dispose()


@pytest.fixture
async def tuned_file_engine(tmp_path):
    """Движок на файловой базе — только там перехватывается открытие транзакции."""
    config = _file_config(tmp_path / "app.sqlite3")
    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    configure_sqlite(engine, config)
    await create_all(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def tuned_memory_engine():
    """Движок на базе в памяти со схемой из моделей и полным набором прагм."""
    config = Config(db_provider="sqlite", db_path=":memory:")
    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    configure_sqlite(engine, config)
    await create_all(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@asynccontextmanager
async def _writing(engine):
    """Соединение с объявленным намерением писать — вне ``write_scope`` его ставим сами."""
    async with engine.connect() as conn:
        await conn.execution_options(**WRITE_EXECUTION_OPTIONS)
        yield conn
        await conn.commit()


async def _add_task_with_log(engine) -> int:
    now = utc_now()
    async with _writing(engine) as conn:
        task_id = (
            await conn.execute(
                insert(CoreTask).values(
                    status=CoreTaskStatus.running, module="m", code="c", started_at=now
                )
            )
        ).inserted_primary_key[0]
        await conn.execute(
            insert(CoreTaskLog).values(
                task_id=task_id, level=CoreTaskLogLevel.info, message="x", created_at=now
            )
        )
    return task_id


@pytest.mark.db
async def test_child_row_without_parent_is_rejected(tuned_memory_engine):
    with pytest.raises(exc.IntegrityError):
        async with _writing(tuned_memory_engine) as conn:
            await conn.execute(
                insert(CoreTaskLog).values(
                    task_id=404,
                    level=CoreTaskLogLevel.info,
                    message="сирота",
                    created_at=utc_now(),
                )
            )


@pytest.mark.db
async def test_declared_cascade_is_executed_by_the_engine(tuned_memory_engine):
    """Каскад объявлен в схеме — с включённой прагмой его исполняет движок, а не CRUD."""
    task_id = await _add_task_with_log(tuned_memory_engine)
    async with _writing(tuned_memory_engine) as conn:
        await conn.execute(text("DELETE FROM core_tasks WHERE id = :id"), {"id": task_id})
        orphans = (await conn.execute(select(CoreTaskLog.id))).all()
    assert orphans == []


@pytest.mark.db
async def test_foreign_keys_disabled_only_for_the_wrapped_block(tuned_memory_engine):
    def check(connection):
        assert foreign_keys_enabled(connection) is True
        with foreign_keys_disabled(connection):
            assert foreign_keys_enabled(connection) is False
        assert foreign_keys_enabled(connection) is True

    async with tuned_memory_engine.connect() as conn:
        await conn.run_sync(check)


@pytest.mark.db
async def test_switching_inside_an_open_transaction_is_refused(tuned_file_engine):
    """Прагма внутри транзакции — пустая операция без ошибки; ловим её чтением обратно."""

    def switch_after_a_statement(connection):
        connection.exec_driver_sql("SELECT 1")
        with foreign_keys_disabled(connection):
            pass

    with pytest.raises(RuntimeError, match="не действует внутри открытой транзакции"):
        async with tuned_file_engine.connect() as conn:
            await conn.run_sync(switch_after_a_statement)


@pytest.mark.db
async def test_transaction_flavour_follows_the_declared_intent(tuned_file_engine):
    opened = []

    @event.listens_for(tuned_file_engine.sync_engine, "before_cursor_execute")
    def record_transaction_start(conn, cursor, statement, parameters, context, many):
        if statement.startswith("BEGIN"):
            opened.append(statement)

    async with tuned_file_engine.connect() as reader:
        await reader.execute(select(CoreTask.id))
    async with tuned_file_engine.connect() as writer:
        await writer.execution_options(**WRITE_EXECUTION_OPTIONS)
        await writer.execute(select(CoreTask.id))

    assert opened == ["BEGIN", "BEGIN IMMEDIATE"]


@pytest.mark.db
async def test_orphans_left_by_the_wrapped_block_raise(tuned_memory_engine):
    """Ради этого проверка и стоит: миграция, уронившая ссылки, не должна пройти молча."""
    task_id = await _add_task_with_log(tuned_memory_engine)

    def drop_parent_row(connection):
        connection.execution_options(**WRITE_EXECUTION_OPTIONS)
        with foreign_keys_disabled(connection):
            connection.exec_driver_sql(f"DELETE FROM core_tasks WHERE id = {task_id}")
            connection.commit()

    with pytest.raises(RuntimeError, match="ссылочной целостности"):
        async with tuned_memory_engine.connect() as conn:
            await conn.run_sync(drop_parent_row)


@pytest.mark.db
async def test_migration_chain_applies_with_foreign_keys_on(tmp_path, monkeypatch):
    """Вся цепочка на файловой базе: три ревизии пересоздают таблицы, дети — на месте."""
    from src.apps.app.modules import build_modules
    from src.core.database import sqlite as sqlite_module
    from src.core.database.migrations import AlembicRunner

    errors = []
    monkeypatch.setattr(
        sqlite_module._LOG, "error", lambda *args, **kwargs: errors.append(args)
    )

    config = _file_config(tmp_path / "app.sqlite3")
    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    configure_sqlite(engine, config)
    runner = AlembicRunner(modules=build_modules())
    try:
        await runner.upgrade_head(engine)
        # Второй прогон накатывать нечего — alembic оставляет открытой транзакцию,
        # в которой читал версии, и проверку надо суметь вернуть всё равно.
        await runner.upgrade_head(engine)
        async with engine.connect() as conn:
            assert (await conn.exec_driver_sql("PRAGMA foreign_keys")).scalar() == 1
            assert (await conn.exec_driver_sql("PRAGMA foreign_key_check")).all() == []
        assert errors == [], "проверку ссылок не удалось вернуть — соединение отбраковано"
    finally:
        await engine.dispose()


@pytest.mark.db
async def test_in_memory_database_stays_usable(tmp_path):
    """У базы в памяти журнал всегда ``memory``; остальные прагмы применяются как есть."""
    config = Config(db_provider="sqlite", db_path=":memory:")
    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    configure_sqlite(engine, config)
    try:
        assert await _read_pragma(engine, "journal_mode") == "memory"
        assert await _read_pragma(engine, "synchronous") == 1
    finally:
        await engine.dispose()
