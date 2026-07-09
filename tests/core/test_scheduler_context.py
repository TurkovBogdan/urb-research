"""Тесты TaskContext-логгера.

TaskContext.{debug,info,warn,error} пишет в core_tasks_logs с правильным level
и форматирует %-args.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from src.core.config import Config
from src.core.crud import tasks as crud_tasks
from src.core.database import close_database, init_database, session_scope
from src.core.locks import CoreLock
from src.core.models.tasks import CoreTaskLog, CoreTaskLogLevel
from src.core.scheduler.context import TaskContext



@pytest.fixture
async def task_id(config: Config):
    """Engine + core-таблицы + одна running запись, к которой цепляются логи."""
    engine = await init_database(config)
    from src.core.database.runtime import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    tid = await crud_tasks.create_running(module="m", code="c")
    try:
        yield tid
    finally:
        await close_database()


def _ctx(task_id: int) -> TaskContext:
    return TaskContext(
        task_id=task_id,
        module="m",
        code="c",
        lock=CoreLock(key="task:m:c", owner=f"task_run:{task_id}"),
    )


@pytest.mark.db
async def test_logger_info_writes_row_with_info_level(task_id: int):
    ctx = _ctx(task_id)
    await ctx.info("hello")
    async with session_scope() as s:
        rows = (await s.execute(select(CoreTaskLog))).scalars().all()
    assert len(rows) == 1
    assert rows[0].level == CoreTaskLogLevel.info
    assert rows[0].message == "hello"
    assert rows[0].task_id == task_id


@pytest.mark.db
async def test_logger_levels_map_to_enum(task_id: int):
    ctx = _ctx(task_id)
    await ctx.debug("d")
    await ctx.info("i")
    await ctx.warn("w")
    await ctx.error("e")
    async with session_scope() as s:
        rows = (
            await s.execute(select(CoreTaskLog).order_by(CoreTaskLog.id))
        ).scalars().all()
    assert [r.level for r in rows] == [
        CoreTaskLogLevel.debug,
        CoreTaskLogLevel.info,
        CoreTaskLogLevel.warn,
        CoreTaskLogLevel.error,
    ]
    assert [r.message for r in rows] == ["d", "i", "w", "e"]


@pytest.mark.db
async def test_logger_formats_percent_args(task_id: int):
    ctx = _ctx(task_id)
    await ctx.info("count=%d name=%s", 42, "x")
    async with session_scope() as s:
        row = (await s.execute(select(CoreTaskLog))).scalar_one()
    assert row.message == "count=42 name=x"


@pytest.mark.db
async def test_logger_truncates_long_message(task_id: int):
    """Сообщение длиннее ``MESSAGE_MAX`` режется до лимита с маркером ``…``."""
    from src.core.crud.tasks_logs import MESSAGE_MAX

    ctx = _ctx(task_id)
    await ctx.info("a" * (MESSAGE_MAX + 100))
    async with session_scope() as s:
        row = (await s.execute(select(CoreTaskLog))).scalar_one()
    assert len(row.message) == MESSAGE_MAX
    assert row.message.endswith("…")
    assert row.message[:-1] == "a" * (MESSAGE_MAX - 1)


@pytest.mark.db
async def test_logger_keeps_message_at_limit(task_id: int):
    """Сообщение ровно по лимиту не трогаем."""
    from src.core.crud.tasks_logs import MESSAGE_MAX

    ctx = _ctx(task_id)
    msg = "a" * MESSAGE_MAX
    await ctx.info(msg)
    async with session_scope() as s:
        row = (await s.execute(select(CoreTaskLog))).scalar_one()
    assert row.message == msg
