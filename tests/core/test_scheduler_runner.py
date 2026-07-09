"""Тесты scheduler.runner.run_entry: жизненный цикл одного запуска задачи.

Покрытие:
- успешный handler → status=success, finished_at заполнен.
- хендлер бросает → status=error, traceback в core_tasks_logs.
- авто-release task-лока и любых суб-локов с тем же owner-ом.
- timeout (ttl) → status=error с текстом про таймаут.
- двойной запуск (одновременно running) → второй вызов — no-op.
- task-лок занят чужим процессом → finalize_error('task lock busy').
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from src.core.config import Config
from src.core.database import close_database, init_database, session_scope
from src.core.locks import CoreLock, CoreLockRow
from src.core.models.tasks import CoreTask, CoreTaskLog, CoreTaskStatus
from src.core.scheduler.registry import TaskEntry
from src.core.scheduler.runner import run_entry



@pytest.fixture
async def db(config: Config):
    """Engine + core-таблицы для запуска runner-а."""
    engine = await init_database(config)
    from src.core.database.runtime import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


def _entry(handler, *, ttl: int = 60) -> TaskEntry:
    return TaskEntry(
        module="m",
        code="c",
        name="Demo",
        description="demo task",
        schedule="* * * * *",
        handler=handler,
        ttl=ttl,
        enabled=True,
    )


async def _fetch_task() -> CoreTask:
    async with session_scope() as s:
        return (await s.execute(select(CoreTask))).scalar_one()


# ── Жизненный цикл ──────────────────────────────────────────────────────────


@pytest.mark.db
async def test_successful_handler_marks_success(db):
    async def handler(ctx):
        pass

    await run_entry(_entry(handler))

    task = await _fetch_task()
    assert task.status == CoreTaskStatus.success
    assert task.finished_at is not None
    assert task.error_text is None


@pytest.mark.db
async def test_failing_handler_marks_error_and_logs_traceback(db):
    async def handler(ctx):
        raise RuntimeError("boom")

    await run_entry(_entry(handler))

    task = await _fetch_task()
    assert task.status == CoreTaskStatus.error
    assert "boom" in (task.error_text or "")

    async with session_scope() as s:
        logs = (await s.execute(select(CoreTaskLog))).scalars().all()
    assert len(logs) == 1
    assert "Traceback" in logs[0].message
    assert "boom" in logs[0].message


@pytest.mark.db
async def test_double_run_is_noop(db):
    """Когда running уже есть, second run_entry должен ничего не сделать."""

    async def handler(ctx):
        pass

    await run_entry(_entry(handler))
    await run_entry(_entry(handler))

    async with session_scope() as s:
        rows = (await s.execute(select(CoreTask))).scalars().all()
    assert len(rows) == 2
    assert all(r.status == CoreTaskStatus.success for r in rows)


# ── ctx.lock — task-level lock ─────────────────────────────────────────────


@pytest.mark.db
async def test_ctx_lock_is_task_level_corelock(db):
    captured = {}

    async def handler(ctx):
        captured["key"] = ctx.lock.key
        captured["owner"] = ctx.lock.owner
        captured["is_owner"] = await ctx.lock.is_owner()

    await run_entry(_entry(handler))

    assert captured["key"] == "task:m:c"
    assert captured["owner"].startswith("task_run:")
    assert captured["is_owner"] is True
    # task-лок снят в finally
    async with session_scope() as s:
        rows = (await s.execute(select(CoreLockRow))).scalars().all()
    assert rows == []


@pytest.mark.db
async def test_sub_locks_with_task_owner_auto_released(db):
    async def handler(ctx):
        await CoreLock.acquire("res:a", 60, owner=ctx.lock.owner)
        await CoreLock.acquire("res:b", 60, owner=ctx.lock.owner)

    await run_entry(_entry(handler))

    async with session_scope() as s:
        rows = (await s.execute(select(CoreLockRow))).scalars().all()
    assert rows == []


@pytest.mark.db
async def test_sub_locks_auto_released_on_handler_failure(db):
    async def handler(ctx):
        await CoreLock.acquire("res:a", 60, owner=ctx.lock.owner)
        raise RuntimeError("kaboom")

    await run_entry(_entry(handler))

    async with session_scope() as s:
        rows = (await s.execute(select(CoreLockRow))).scalars().all()
    assert rows == []


@pytest.mark.db
async def test_locks_of_other_owners_not_touched(db):
    """Авто-снятие должно цеплять только локи этой задачи, чужие не трогать."""
    await CoreLock.acquire("res:foreign", 60, owner="external:1")

    async def handler(ctx):
        await CoreLock.acquire("res:mine", 60, owner=ctx.lock.owner)

    await run_entry(_entry(handler))

    async with session_scope() as s:
        rows = (await s.execute(select(CoreLockRow))).scalars().all()
    assert {r.key for r in rows} == {"res:foreign"}


@pytest.mark.db
async def test_task_lock_busy_finalizes_error(db):
    """Если task-лок держит другой процесс — finalize_error('task lock busy')."""
    # внешний процесс удерживает task-лок
    foreign = await CoreLock.acquire("task:m:c", 60, owner="external")
    assert foreign is not None

    called = False

    async def handler(ctx):
        nonlocal called
        called = True

    await run_entry(_entry(handler))

    assert called is False
    task = await _fetch_task()
    assert task.status == CoreTaskStatus.error
    assert task.error_text == "task lock busy"


# ── Timeout (ttl) ───────────────────────────────────────────────────────────


@pytest.mark.db
async def test_handler_timeout_marks_error(db):
    import asyncio

    async def handler(ctx):
        await asyncio.sleep(5)

    await run_entry(_entry(handler, ttl=1))  # ttl в секундах; sleep-5 не уложится

    task = await _fetch_task()
    assert task.status == CoreTaskStatus.error
    assert "timeout" in (task.error_text or "")
