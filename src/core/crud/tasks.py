"""CRUD для core_tasks. ORM-модели не пересекают границу слоя.

Каждая функция сама открывает ``session_scope`` и коммитит — каллер передаёт
только данные. Возвращаются detached ORM-row'ы / простые типы; ``expire_on_commit=False``
гарантирует, что атрибуты доступны после выхода из сессии.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import session_scope
from src.core.models.tasks import CoreTask, CoreTaskStatus
from src.core.utils.date import utc_now

ERROR_TEXT_MAX = 512  # лимит ``core_tasks.error_text`` (String(512))


def _truncate(s: str, limit: int) -> str:
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _insert_for(session: AsyncSession):
    dialect = session.bind.dialect.name if session.bind else "postgresql"
    if dialect == "sqlite":
        return sqlite_insert
    return pg_insert


async def create_running(*, module: str, code: str) -> int | None:
    """INSERT с ON CONFLICT DO NOTHING по partial unique индексу.

    Возвращает id новой записи или None, если уже есть running для (module, code).
    """
    async with session_scope() as s:
        insert = _insert_for(s)
        now = utc_now()
        stmt = (
            insert(CoreTask)
            .values(
                status=CoreTaskStatus.running,
                module=module,
                code=code,
                started_at=now,
                heartbeat_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=["module", "code"],
                index_where=text("status = 'running'"),
            )
            .returning(CoreTask.id)
        )
        result = await s.execute(stmt)
        return result.scalar_one_or_none()


async def update_heartbeat(task_id: int) -> None:
    async with session_scope() as s:
        await s.execute(
            update(CoreTask).where(CoreTask.id == task_id).values(heartbeat_at=utc_now())
        )


async def update_payload(task_id: int, payload: dict) -> None:
    async with session_scope() as s:
        await s.execute(
            update(CoreTask).where(CoreTask.id == task_id).values(payload=payload)
        )


async def finalize_success(task_id: int) -> None:
    async with session_scope() as s:
        await s.execute(
            update(CoreTask)
            .where(CoreTask.id == task_id)
            .values(status=CoreTaskStatus.success, finished_at=utc_now())
        )


async def finalize_error(task_id: int, *, text: str) -> None:
    async with session_scope() as s:
        await s.execute(
            update(CoreTask)
            .where(CoreTask.id == task_id)
            .values(
                status=CoreTaskStatus.error,
                error_text=_truncate(text, ERROR_TEXT_MAX),
                finished_at=utc_now(),
            )
        )


async def cleanup_zombies(threshold_seconds: int) -> list[int]:
    """Финализировать зависшие running-записи. Возвращает их id для cleanup локов."""
    async with session_scope() as s:
        cutoff = utc_now() - timedelta(seconds=threshold_seconds)
        stmt = (
            update(CoreTask)
            .where(
                CoreTask.status == CoreTaskStatus.running,
                (CoreTask.heartbeat_at.is_(None)) | (CoreTask.heartbeat_at < cutoff),
            )
            .values(
                status=CoreTaskStatus.error,
                error_text="orphaned: stale heartbeat",
                finished_at=utc_now(),
            )
            .returning(CoreTask.id)
        )
        result = await s.execute(stmt)
        return [row[0] for row in result.all()]


def _stats_row(by_status: dict[str, int]) -> dict[str, int]:
    return {
        "total": sum(by_status.values()),
        "success": by_status.get("success", 0),
        "error": by_status.get("error", 0),
        "running": by_status.get("running", 0),
    }


async def stats_24h(*, module: str, code: str) -> dict[str, int]:
    """Считает запуски за последние 24 часа: total / success / error / running."""
    async with session_scope() as s:
        cutoff = utc_now() - timedelta(hours=24)
        stmt = (
            select(CoreTask.status, func.count())
            .where(
                CoreTask.module == module,
                CoreTask.code == code,
                CoreTask.started_at >= cutoff,
            )
            .group_by(CoreTask.status)
        )
        result = await s.execute(stmt)
        by_status = {status.value: cnt for status, cnt in result.all()}
    return _stats_row(by_status)


async def stats_24h_all() -> dict[tuple[str, str], dict[str, int]]:
    """Статистика за 24 часа сразу для всех (module, code) — один GROUP BY.

    Заменяет N запросов из ``stats_24h`` на один: дашборд задач строится без
    N+1 round-trip'ов к БД. Ключ результата — пара ``(module, code)``; пары без
    запусков за окно в словаре отсутствуют (каллер подставляет нули).
    """
    async with session_scope() as s:
        cutoff = utc_now() - timedelta(hours=24)
        stmt = (
            select(CoreTask.module, CoreTask.code, CoreTask.status, func.count())
            .where(CoreTask.started_at >= cutoff)
            .group_by(CoreTask.module, CoreTask.code, CoreTask.status)
        )
        result = await s.execute(stmt)
        per_pair: dict[tuple[str, str], dict[str, int]] = {}
        for module, code, status, cnt in result.all():
            per_pair.setdefault((module, code), {})[status.value] = cnt
    return {pair: _stats_row(by_status) for pair, by_status in per_pair.items()}


# Колонки, по которым разрешена серверная сортировка runs.
# duration = finished_at - started_at (NULL у running — уходит в конец/начало).
_RUN_DURATION = CoreTask.finished_at - CoreTask.started_at
_SORTABLE = {
    "id": CoreTask.id,
    "status": CoreTask.status,
    "started_at": CoreTask.started_at,
    "finished_at": CoreTask.finished_at,
    "duration": _RUN_DURATION,
}


async def list_runs(
    *,
    module: str,
    code: str,
    limit: int = 50,
    offset: int = 0,
    status: CoreTaskStatus | None = None,
    sort_by: str = "started_at",
    sort_dir: str = "desc",
) -> tuple[list[CoreTask], int]:
    """Запуски задачи + общее количество с учётом фильтра.

    Сортировка серверная по всему набору (не по текущей странице): ``sort_by`` из
    ``_SORTABLE`` (иначе fallback на ``started_at``), ``sort_dir`` = asc|desc.
    """
    where = [CoreTask.module == module, CoreTask.code == code]
    if status is not None:
        where.append(CoreTask.status == status)

    col = _SORTABLE.get(sort_by, CoreTask.started_at)
    order = col.desc().nullslast() if sort_dir == "desc" else col.asc().nullsfirst()

    rows_stmt = (
        select(CoreTask)
        .where(*where)
        .order_by(order, CoreTask.id.desc())
        .limit(limit)
        .offset(offset)
    )
    count_stmt = select(func.count()).select_from(CoreTask).where(*where)

    async with session_scope() as s:
        rows = list((await s.execute(rows_stmt)).scalars().all())
        total = int((await s.execute(count_stmt)).scalar_one())
    return rows, total


async def get_running_set() -> set[tuple[str, str]]:
    """Все (module, code) пары с активным running-запуском."""
    async with session_scope() as s:
        result = await s.execute(
            select(CoreTask.module, CoreTask.code).where(
                CoreTask.status == CoreTaskStatus.running
            )
        )
        return {(row[0], row[1]) for row in result.all()}


async def first_run_since(
    module: str, code: str, since: datetime
) -> tuple[int, CoreTaskStatus] | None:
    """Самый ранний запуск пары, стартовавший не раньше ``since``: (id, status)."""
    stmt = (
        select(CoreTask.id, CoreTask.status)
        .where(
            CoreTask.module == module,
            CoreTask.code == code,
            CoreTask.started_at >= since,
        )
        .order_by(CoreTask.started_at.asc())
        .limit(1)
    )
    async with session_scope() as s:
        row = (await s.execute(stmt)).first()
        return (row[0], row[1]) if row is not None else None


async def statuses_by_ids(task_ids: list[int]) -> dict[int, CoreTaskStatus]:
    if not task_ids:
        return {}
    stmt = select(CoreTask.id, CoreTask.status).where(CoreTask.id.in_(task_ids))
    async with session_scope() as s:
        result = await s.execute(stmt)
        return {row[0]: row[1] for row in result.all()}


async def brief_status_all() -> dict[tuple[str, str], tuple[CoreTaskStatus, datetime | None]]:
    """Краткий статус каждой (module, code): статус последнего запуска + время последнего успешного.

    Значение — пара ``(last_status, last_completed_at)``: статус самого свежего
    запуска (по ``started_at``) и ``finished_at`` самого свежего успешного запуска
    (``None``, если успеха ещё не было). Пары без единого запуска в словаре
    отсутствуют — каллер трактует их как «ещё не запускалась».
    """
    rank = func.row_number().over(
        partition_by=(CoreTask.module, CoreTask.code),
        order_by=CoreTask.started_at.desc(),
    )
    ranked = select(CoreTask.module, CoreTask.code, CoreTask.status, rank.label("rank")).subquery()
    latest_stmt = select(ranked.c.module, ranked.c.code, ranked.c.status).where(ranked.c.rank == 1)
    last_success_stmt = (
        select(CoreTask.module, CoreTask.code, func.max(CoreTask.finished_at))
        .where(CoreTask.status == CoreTaskStatus.success)
        .group_by(CoreTask.module, CoreTask.code)
    )
    async with session_scope() as s:
        latest = {(m, c): status for m, c, status in (await s.execute(latest_stmt)).all()}
        last_completed = {(m, c): fin for m, c, fin in (await s.execute(last_success_stmt)).all()}
    return {pair: (status, last_completed.get(pair)) for pair, status in latest.items()}


async def last_run_at(module: str, code: str) -> datetime | None:
    stmt = (
        select(CoreTask.started_at)
        .where(
            CoreTask.module == module,
            CoreTask.code == code,
            CoreTask.status.in_([CoreTaskStatus.success, CoreTaskStatus.error]),
        )
        .order_by(CoreTask.started_at.desc())
        .limit(1)
    )
    async with session_scope() as s:
        result = await s.execute(stmt)
        return result.scalar_one_or_none()


__all__ = [
    "create_running",
    "update_heartbeat",
    "update_payload",
    "finalize_success",
    "finalize_error",
    "cleanup_zombies",
    "brief_status_all",
    "first_run_since",
    "get_running_set",
    "statuses_by_ids",
    "stats_24h",
    "stats_24h_all",
    "list_runs",
    "last_run_at",
]
