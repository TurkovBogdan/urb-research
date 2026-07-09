"""CRUD ``WebSearchQuery`` — прогоны поиска. Каждая функция владеет сессией.

Первичный ключ — голый 22-hex код (``query_code``). Ретраев/очереди нет:
исполнение синхронное. Машина состояний ``pending → processing → done | error``: строка
создаётся в ``pending``, ``query_mark_processing`` переводит в ``processing``, финал —
``query_finish`` (``done``, в т.ч. без результатов) или ``query_mark_error`` (``error``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.sql.selectable import Select

from src.core.database import session_scope
from src.core.utils.date import utc_now
from src.core.utils.hashing import random_hash
from src.modules.web_search.constants import (
    SEARCH_STATUS_DONE,
    SEARCH_STATUS_ERROR,
    SEARCH_STATUS_PENDING,
    SEARCH_STATUS_PROCESSING,
)
from src.modules.web_search.models.query import WebSearchQuery

def query_code() -> str:
    """Код прогона — голый 22-hex ``random_hash`` (у прогона поиска нет естественного ключа).

    web_search коды не типизирует — агентские префиксы живут в модуле research.
    """
    return random_hash()


async def query_create(
    *,
    search_engine: str,
    fetch_engine: str,
    query: str,
    params: Any | None = None,
) -> WebSearchQuery:
    async with session_scope() as s:
        row = WebSearchQuery(
            code=query_code(),
            search_engine=search_engine,
            fetch_engine=fetch_engine,
            query=query,
            params=params,
            status=SEARCH_STATUS_PENDING,
        )
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


async def query_get(code: str) -> WebSearchQuery | None:
    async with session_scope() as s:
        return await s.get(WebSearchQuery, code)


async def query_mark_processing(code: str) -> WebSearchQuery | None:
    """Перевести прогон в ``processing``: начались поиск и получение контента страниц."""
    now = utc_now()
    stmt = (
        update(WebSearchQuery)
        .where(WebSearchQuery.code == code)
        .values(status=SEARCH_STATUS_PROCESSING, updated_at=now)
        .returning(WebSearchQuery)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


async def query_finish(code: str) -> WebSearchQuery | None:
    """Финализировать прогон статусом ``done`` (даже если результатов не нашлось)."""
    now = utc_now()
    stmt = (
        update(WebSearchQuery)
        .where(WebSearchQuery.code == code)
        .values(status=SEARCH_STATUS_DONE, finished_at=now, error=None, updated_at=now)
        .returning(WebSearchQuery)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


async def query_mark_error(
    code: str, *, error: str | None = None
) -> WebSearchQuery | None:
    """Терминальная ошибка движка: статус ``error`` + код ошибки (без повторов)."""
    now = utc_now()
    stmt = (
        update(WebSearchQuery)
        .where(WebSearchQuery.code == code)
        .values(status=SEARCH_STATUS_ERROR, error=error, finished_at=now, updated_at=now)
        .returning(WebSearchQuery)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


async def query_processing_count(search_engine: str, *, since: datetime) -> int:
    """Сколько поисков этого движка сейчас в работе: свежие ``processing`` (``updated_at >= since``).

    Залипшие (старее ``since``) не считаются — иначе краш процесса держал бы слот вечно.
    """
    stmt = (
        select(func.count())
        .select_from(WebSearchQuery)
        .where(
            WebSearchQuery.search_engine == search_engine,
            WebSearchQuery.status == SEARCH_STATUS_PROCESSING,
            WebSearchQuery.updated_at >= since,
        )
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalar_one()


async def query_expire_stale(search_engine: str, *, before: datetime) -> int:
    """Добить залипшие ``processing`` этого движка (``updated_at < before``, краш процесса) → ``error``.

    Reaper без планировщика: зовётся из гейта слотов перед подсчётом. Возвращает число добитых.
    """
    now = utc_now()
    stmt = (
        update(WebSearchQuery)
        .where(
            WebSearchQuery.search_engine == search_engine,
            WebSearchQuery.status == SEARCH_STATUS_PROCESSING,
            WebSearchQuery.updated_at < before,
        )
        .values(status=SEARCH_STATUS_ERROR, error="stale", finished_at=now, updated_at=now)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).rowcount or 0


def _query_filtered(
    *, query: str | None, status: str | None, search_engine: str | None
) -> Select:
    stmt = select(WebSearchQuery)
    if query:
        stmt = stmt.where(WebSearchQuery.query.ilike(f"%{query}%"))
    if status:
        stmt = stmt.where(WebSearchQuery.status == status)
    if search_engine:
        stmt = stmt.where(WebSearchQuery.search_engine == search_engine)
    return stmt


# Колонки, по которым допустима сортировка списка (белый список = защита от инъекции:
# неизвестный ключ падает в дефолт ``created_at``). Совпадают с sortable-заголовками фронта.
QUERY_SORT_COLUMNS = {
    "created_at": WebSearchQuery.created_at,
    "finished_at": WebSearchQuery.finished_at,
    "status": WebSearchQuery.status,
    "search_engine": WebSearchQuery.search_engine,
    "fetch_engine": WebSearchQuery.fetch_engine,
    "query": WebSearchQuery.query,
}


async def query_list(
    *,
    query: str | None = None,
    status: str | None = None,
    search_engine: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    offset: int = 0,
    limit: int = 50,
) -> list[WebSearchQuery]:
    """Прогоны с фильтрами (текст по ``query``, статус, движок поиска), новые сверху.

    Сортировка — по колонке из ``QUERY_SORT_COLUMNS`` (неизвестная → ``created_at``);
    ``code`` — стабильный тайбрейк в ту же сторону (числового id больше нет).
    """
    column = QUERY_SORT_COLUMNS.get(sort_by, WebSearchQuery.created_at)
    ascending = sort_dir == "asc"
    order = (
        (column.asc(), WebSearchQuery.code.asc())
        if ascending
        else (column.desc(), WebSearchQuery.code.desc())
    )
    stmt = (
        _query_filtered(query=query, status=status, search_engine=search_engine)
        .order_by(*order)
        .offset(offset)
        .limit(limit)
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def query_count(
    *, query: str | None = None, status: str | None = None, search_engine: str | None = None
) -> int:
    stmt = _query_filtered(query=query, status=status, search_engine=search_engine)
    async with session_scope() as s:
        return (
            await s.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()


__all__ = [
    "query_create",
    "query_get",
    "query_mark_processing",
    "query_finish",
    "query_mark_error",
    "query_processing_count",
    "query_expire_stale",
    "query_list",
    "query_count",
]
