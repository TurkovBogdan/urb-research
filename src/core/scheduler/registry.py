"""Реестр зарегистрированных задач — модуль-глобальный singleton."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.scheduler.context import TaskContext


TaskHandler = Callable[["TaskContext"], Awaitable[None]]


@dataclass(frozen=True)
class TaskEntry:
    module: str
    code: str
    name: str          # человекочитаемое название для UI
    description: str   # описание для UI
    schedule: str | None  # 5-польный cron; None → автозапуск отключён
    handler: TaskHandler
    ttl: int           # секунды; одновременно timeout хендлера и TTL task-лока
    enabled: bool      # false → тикер пропускает задачу при обходе реестра
    user_request: bool = False  # true → задача принимает запросы от пользователя
    sort: int = 500           # порядок вывода в UI; не влияет на выполнение


class TaskRegistry:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], TaskEntry] = {}

    def register(
        self,
        *,
        module: str,
        code: str,
        name: str,
        description: str,
        schedule: str | None,
        handler: TaskHandler,
        ttl: int,
        enabled: bool,
        user_request: bool = False,
        sort: int = 500,
    ) -> None:
        key = (module, code)
        if key in self._entries:
            raise ValueError(f"task already registered: {module}.{code}")
        self._entries[key] = TaskEntry(
            module, code, name, description, schedule, handler, ttl, enabled, user_request, sort
        )

    def all(self) -> list[TaskEntry]:
        return list(self._entries.values())

    def get(self, module: str, code: str) -> TaskEntry | None:
        return self._entries.get((module, code))

    def clear(self) -> None:
        self._entries.clear()


_REGISTRY = TaskRegistry()


def get_registry() -> TaskRegistry:
    return _REGISTRY


__all__ = ["TaskEntry", "TaskHandler", "TaskRegistry", "get_registry"]
