"""Heartbeat: маркер живого планировщика."""

from __future__ import annotations

from src.core.scheduler import CoreTaskBase, TaskContext


class HeartbeatTask(CoreTaskBase):
    """Сам факт записи success в core_tasks — сигнал живости планировщика."""

    MODULE = "core"
    CODE = "heartbeat"
    NAME = "Heartbeat"
    DESCRIPTION = (
        "Маркер живого планировщика: каждую минуту пишет успешный запуск "
        "в core_tasks."
    )
    SCHEDULE = "* * * * *"
    TTL = 30

    @staticmethod
    async def handle(ctx: TaskContext) -> None:
        return None


__all__ = ["HeartbeatTask"]
