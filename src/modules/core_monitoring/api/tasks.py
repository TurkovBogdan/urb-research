"""Раздел «Задачи» — HTTP-эндпойнты scheduler-задач.

Список задач (+ статистика за 24 часа), одна задача, её запуски (пагинация +
фильтр статуса + серверная сортировка) и логи одного запуска. Корень ``/tasks``
прописан прямо в путях маршрутов (агрегатор включает роутер без prefix). Зона
internal в чистом ядре = ``allow_all`` — guard не нужен.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.core.crud import tasks as crud_tasks
from src.core.crud import tasks_logs as crud_tasks_logs
from src.core.models.tasks import CoreTaskStatus
from src.core.scheduler.registry import get_registry
from src.core.utils.date import DatetimeUTCStr


class TaskStats24h(BaseModel):
    total: int
    success: int
    error: int
    running: int


class TaskInfo(BaseModel):
    module: str
    code: str
    name: str
    description: str
    schedule: str | None
    ttl: int
    enabled: bool
    user_request: bool
    sort: int
    stats_24h: TaskStats24h


class TaskRunInfo(BaseModel):
    id: int
    status: str
    started_at: DatetimeUTCStr
    finished_at: DatetimeUTCStr | None
    heartbeat_at: DatetimeUTCStr | None
    error_text: str | None
    payload: dict | None


class TaskRunsPage(BaseModel):
    items: list[TaskRunInfo]
    total: int


class TaskRunLog(BaseModel):
    id: int
    level: str
    message: str
    created_at: DatetimeUTCStr


router = APIRouter()


_ZERO_STATS = {"total": 0, "success": 0, "error": 0, "running": 0}


def _to_info(entry, stats: dict[str, int]) -> TaskInfo:
    return TaskInfo(
        module=entry.module,
        code=entry.code,
        name=entry.name,
        description=entry.description,
        schedule=entry.schedule,
        ttl=entry.ttl,
        enabled=entry.enabled,
        user_request=entry.user_request,
        sort=entry.sort,
        stats_24h=TaskStats24h(**stats),
    )


def _module_rank(module: str) -> int:
    """core → core_* → остальные модули."""
    if module == "core":
        return 0
    if module.startswith("core_"):
        return 1
    return 2


@router.get("/tasks", response_model=list[TaskInfo])
async def list_tasks() -> list[TaskInfo]:
    """Все зарегистрированные scheduler-задачи + статистика за 24 часа."""
    entries = sorted(
        get_registry().all(),
        key=lambda e: (_module_rank(e.module), e.module, e.sort),
    )
    stats = await crud_tasks.stats_24h_all()
    return [_to_info(e, stats.get((e.module, e.code), _ZERO_STATS)) for e in entries]


@router.get("/tasks/{module}/{code}", response_model=TaskInfo)
async def get_task(module: str, code: str) -> TaskInfo:
    for e in get_registry().all():
        if e.module == module and e.code == code:
            stats = await crud_tasks.stats_24h(module=module, code=code)
            return _to_info(e, stats)
    raise HTTPException(status_code=404, detail="task not registered")


@router.get("/tasks/{module}/{code}/runs", response_model=TaskRunsPage)
async def list_task_runs(
    module: str,
    code: str,
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: CoreTaskStatus | None = None,
    sort_by: str = Query("started_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
) -> TaskRunsPage:
    """Запуски задачи с пагинацией + фильтр статуса + серверная сортировка."""
    rows, total = await crud_tasks.list_runs(
        module=module, code=code, limit=limit, offset=offset, status=status,
        sort_by=sort_by, sort_dir=sort_dir,
    )
    return TaskRunsPage(
        items=[
            TaskRunInfo(
                id=r.id,
                status=r.status.value,
                started_at=r.started_at,
                finished_at=r.finished_at,
                heartbeat_at=r.heartbeat_at,
                error_text=r.error_text,
                payload=r.payload,
            )
            for r in rows
        ],
        total=total,
    )


@router.get("/tasks/{module}/{code}/runs/{run_id}/logs", response_model=list[TaskRunLog])
async def list_task_run_logs(module: str, code: str, run_id: int) -> list[TaskRunLog]:
    """Логи одного запуска задачи (created_at asc)."""
    rows = await crud_tasks_logs.list_for_task(task_id=run_id, module=module, code=code)
    return [
        TaskRunLog(
            id=r.id,
            level=r.level.value,
            message=r.message,
            created_at=r.created_at,
        )
        for r in rows
    ]


__all__ = ["router"]
