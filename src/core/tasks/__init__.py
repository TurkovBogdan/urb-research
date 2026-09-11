"""Системные задачи ядра. Регистрируется ``app_factory.create_app``."""

from __future__ import annotations

from src.core.scheduler.registry import get_registry
from src.core.tasks.heartbeat_task import HeartbeatTask
from src.core.tasks.sqlite_health_task import SqliteHealthTask

_MODULE = "core"
_TASKS = (HeartbeatTask, SqliteHealthTask)


def register() -> None:
    """Зарегистрировать все задачи ядра. Идемпотентно."""
    registry = get_registry()
    for task in _TASKS:
        if registry.get(_MODULE, task.CODE) is None:
            task.register()


__all__ = ["register"]
