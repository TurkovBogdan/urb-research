"""``crud.tasks.finalize_error``: усечение ``error_text`` по лимиту колонки."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from src.core.config import Config
from src.core.crud import tasks as crud_tasks
from src.core.crud.tasks import ERROR_TEXT_MAX
from src.core.database import close_database, init_database, session_scope
from src.core.models.tasks import CoreTask



@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    from src.core.database.runtime import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.mark.db
async def test_finalize_error_truncates_long_text(db):
    tid = await crud_tasks.create_running(module="m", code="c")
    await crud_tasks.finalize_error(tid, text="x" * (ERROR_TEXT_MAX + 200))

    async with session_scope() as s:
        row = (await s.execute(select(CoreTask).where(CoreTask.id == tid))).scalar_one()

    assert len(row.error_text) == ERROR_TEXT_MAX
    assert row.error_text.endswith("…")
    assert row.error_text[:-1] == "x" * (ERROR_TEXT_MAX - 1)


@pytest.mark.db
async def test_finalize_error_keeps_text_at_limit(db):
    tid = await crud_tasks.create_running(module="m", code="c")
    text = "x" * ERROR_TEXT_MAX
    await crud_tasks.finalize_error(tid, text=text)

    async with session_scope() as s:
        row = (await s.execute(select(CoreTask).where(CoreTask.id == tid))).scalar_one()

    assert row.error_text == text


@pytest.mark.db
async def test_stats_24h_all_aggregates_per_pair(db):
    # pair (m, a): один success + один error; pair (m, b): один running.
    t1 = await crud_tasks.create_running(module="m", code="a")
    await crud_tasks.finalize_success(t1)
    t2 = await crud_tasks.create_running(module="m", code="a")
    await crud_tasks.finalize_error(t2, text="boom")
    await crud_tasks.create_running(module="m", code="b")

    stats = await crud_tasks.stats_24h_all()

    assert stats[("m", "a")] == {"total": 2, "success": 1, "error": 1, "running": 0}
    assert stats[("m", "b")] == {"total": 1, "success": 0, "error": 0, "running": 1}
    # Совпадает с поштучным stats_24h и не содержит лишних пар.
    assert stats[("m", "a")] == await crud_tasks.stats_24h(module="m", code="a")
    assert ("m", "missing") not in stats
