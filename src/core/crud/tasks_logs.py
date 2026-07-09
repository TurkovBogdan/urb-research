"""CRUD для core_tasks_logs."""

from __future__ import annotations

from sqlalchemy import select

from src.core.database import session_scope
from src.core.models.tasks import CoreTask, CoreTaskLog, CoreTaskLogLevel
from src.core.utils.date import utc_now

MESSAGE_MAX = 1024  # лимит ``core_tasks_logs.message`` (String(1024))


async def create(*, task_id: int, level: CoreTaskLogLevel, message: str) -> None:
    if len(message) > MESSAGE_MAX:
        message = message[: MESSAGE_MAX - 1] + "…"
    async with session_scope() as s:
        s.add(
            CoreTaskLog(
                task_id=task_id,
                level=level,
                message=message,
                created_at=utc_now(),
            )
        )


async def list_for_task(
    *, task_id: int, module: str, code: str
) -> list[CoreTaskLog]:
    """Логи запуска по id; module/code — защита от обращения к чужому task_id."""
    stmt = (
        select(CoreTaskLog)
        .join(CoreTask, CoreTask.id == CoreTaskLog.task_id)
        .where(
            CoreTaskLog.task_id == task_id,
            CoreTask.module == module,
            CoreTask.code == code,
        )
        .order_by(CoreTaskLog.created_at.asc(), CoreTaskLog.id.asc())
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


__all__ = ["create", "list_for_task"]
