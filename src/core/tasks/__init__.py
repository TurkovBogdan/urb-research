"""Системные задачи ядра. Регистрируется ``app_factory.create_app``."""

from __future__ import annotations

from src.core.scheduler.registry import get_registry
from src.core.tasks.heartbeat_task import HeartbeatTask

_MODULE = "core"


def register() -> None:
    """Зарегистрировать все задачи ядра. Идемпотентно."""
    registry = get_registry()
    if registry.get(_MODULE, "heartbeat") is None:
        HeartbeatTask.register()


__all__ = ["register"]
