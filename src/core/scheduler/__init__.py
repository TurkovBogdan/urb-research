"""Публичный API планировщика задач ядра."""

from __future__ import annotations

from src.core.config import Config
from src.core.scheduler.context import TaskContext
from src.core.scheduler.registry import (
    TaskEntry,
    TaskHandler,
    TaskRegistry,
    get_registry,
)
from src.core.scheduler.runner import run_entry
from src.core.scheduler.task_base import CoreTaskBase
from src.core.scheduler.ticker import Ticker


_TICKER: Ticker | None = None
# Override от worker-процесса: форсирует запуск тикера (минуя worker_enabled) и
# задаёт scope/ручки. Выставляется точкой входа (src/app.py) ДО lifespan.
_WORKER_OVERRIDE: dict | None = None


def configure_worker(
    *,
    modules: frozenset[str] | None,
    max_concurrent: int,
    tick: int,
) -> None:
    """Сконфигурировать процесс как worker: форс-старт тикера + scope модулей.

    Зовётся точкой входа чистого worker-процесса до старта lifespan. После этого
    ``start()`` поднимет тикер независимо от ``config.worker_enabled``.
    """
    global _WORKER_OVERRIDE
    _WORKER_OVERRIDE = {
        "modules": modules,
        "max_concurrent": max_concurrent,
        "tick": tick,
    }


def register(
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
    """Регистрация задачи. ``schedule`` — стандартный 5-польный cron; None → только по запросу."""
    get_registry().register(
        module=module,
        code=code,
        name=name,
        description=description,
        schedule=schedule,
        handler=handler,
        ttl=ttl,
        enabled=enabled,
        user_request=user_request,
        sort=sort,
    )


async def start(config: Config) -> None:
    """Поднять тикер. Источник параметров: worker-override (если задан) либо config.

    Без override тикер стартует только при ``config.worker_enabled`` (встроенный
    режим dev). Override (чистый worker-процесс) форсит старт и задаёт scope.
    """
    global _TICKER
    if _TICKER is not None:
        return
    if _WORKER_OVERRIDE is not None:
        ov = _WORKER_OVERRIDE
        _TICKER = Ticker(
            tick_seconds=ov["tick"],
            max_concurrent_runs=ov["max_concurrent"],
            modules=ov["modules"],
        )
    elif config.worker_enabled:
        _TICKER = Ticker(
            tick_seconds=config.worker_tick_seconds,
            max_concurrent_runs=config.worker_max_concurrent_runs,
            modules=config.worker_modules_set,
        )
    else:
        return
    await _TICKER.start()


async def stop() -> None:
    global _TICKER, _WORKER_OVERRIDE
    _WORKER_OVERRIDE = None
    if _TICKER is None:
        return
    await _TICKER.stop()
    _TICKER = None


__all__ = [
    "CoreTaskBase",
    "TaskContext",
    "TaskEntry",
    "TaskHandler",
    "TaskRegistry",
    "Ticker",
    "configure_worker",
    "get_registry",
    "register",
    "run_entry",
    "start",
    "stop",
]
