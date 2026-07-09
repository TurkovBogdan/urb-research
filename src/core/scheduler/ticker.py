"""Тик-цикл: каждые N секунд проверяет реестр и спавнит готовые задачи."""

from __future__ import annotations

import asyncio
from datetime import datetime

from croniter import croniter

from src.core.crud import tasks as crud_tasks
from src.core.locks import release_for_owners
from src.core.loggers import get_logger

_LOG = get_logger("tasks")
from src.core.scheduler.registry import TaskEntry, get_registry
from src.core.scheduler.runner import run_entry
from src.core.utils.date import utc_now


def is_due(expression: str, now: datetime, last_run_at: datetime | None) -> bool:
    """Пора ли запускать задачу. ``expression`` — стандартный 5-польный cron."""
    if last_run_at is None:
        return True
    return croniter(expression, last_run_at).get_next(datetime) <= now


class Ticker:
    """Один тик: cleanup zombies → итерация реестра → спавн готовых через семафор."""

    def __init__(
        self,
        *,
        tick_seconds: int = 5,
        zombie_threshold: int = 90,
        shutdown_grace_seconds: int = 30,
        max_concurrent_runs: int = 10,
        modules: frozenset[str] | None = None,
    ) -> None:
        self.tick_seconds = tick_seconds
        self.zombie_threshold = zombie_threshold
        self.shutdown_grace_seconds = shutdown_grace_seconds
        # Scope: гонять задачи только этих модулей; None — весь реестр.
        self.modules = modules
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._active: set[asyncio.Task] = set()
        self._semaphore = asyncio.Semaphore(max_concurrent_runs)

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Остановить тик, дождаться активных run_entry до grace, потом отменить."""
        self._stop.set()
        if self._task is not None:
            try:
                await self._task
            finally:
                self._task = None
        if self._active:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._active, return_exceptions=True),
                    timeout=self.shutdown_grace_seconds,
                )
            except asyncio.TimeoutError:
                _LOG.warning(
                    "scheduler shutdown grace exceeded, cancelling %d active runs",
                    len(self._active),
                )
                for t in self._active:
                    t.cancel()
                await asyncio.gather(*self._active, return_exceptions=True)

    def _spawn(self, entry: TaskEntry) -> None:
        task = asyncio.create_task(self._guarded_run(entry))
        self._active.add(task)
        task.add_done_callback(self._active.discard)

    async def _guarded_run(self, entry: TaskEntry) -> None:
        async with self._semaphore:
            try:
                await run_entry(entry)
            except Exception:
                _LOG.exception(
                    "run_entry crashed for %s.%s", entry.module, entry.code
                )

    async def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                await self._tick_once()
            except Exception:
                _LOG.exception("scheduler tick failed")
            try:
                await asyncio.wait_for(
                    self._stop.wait(), timeout=self.tick_seconds
                )
            except asyncio.TimeoutError:
                pass

    async def _tick_once(self) -> None:
        zombie_ids = await crud_tasks.cleanup_zombies(self.zombie_threshold)
        if zombie_ids:
            await release_for_owners([f"task_run:{i}" for i in zombie_ids])
            _LOG.warning(
                "scheduler cleaned %d zombie tasks", len(zombie_ids)
            )

        now = utc_now()
        for entry in get_registry().all():
            if self.modules is not None and entry.module not in self.modules:
                continue
            if not entry.enabled:
                continue
            if entry.schedule is None:
                continue
            last = await crud_tasks.last_run_at(entry.module, entry.code)
            if not is_due(entry.schedule, now, last):
                continue
            self._spawn(entry)


__all__ = ["Ticker"]
