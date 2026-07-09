"""CRUD ``WebSearchQueryResult`` — результаты запроса (связь запрос ↔ документ по кодам)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.core.database import session_scope
from src.core.utils.date import utc_now
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query_result import WebSearchQueryResult


async def result_add(
    *,
    query_code: str,
    page_code: str,
    rank: int | None = None,
    score: float | None = None,
    summary: str | None = None,
    meta: Any | None = None,
) -> None:
    """Добавить строку выдачи; дубль ``(query_code, page_code)`` тихо пропускается."""
    now = utc_now()
    async with session_scope() as s:
        dialect = s.bind.dialect.name if s.bind else "postgresql"
        insert = sqlite_insert if dialect == "sqlite" else pg_insert
        stmt = (
            insert(WebSearchQueryResult)
            .values(
                query_code=query_code,
                page_code=page_code,
                rank=rank,
                score=score,
                summary=summary,
                meta=meta,
                created_at=now,
            )
            .on_conflict_do_nothing(index_elements=["query_code", "page_code"])
        )
        await s.execute(stmt)


async def results_for_query(query_code: str) -> list[WebSearchQueryResult]:
    async with session_scope() as s:
        rows = (
            await s.execute(
                select(WebSearchQueryResult)
                .where(WebSearchQueryResult.query_code == query_code)
                .order_by(WebSearchQueryResult.rank, WebSearchQueryResult.id)
            )
        ).scalars().all()
    return list(rows)


async def results_with_page_for_query(
    query_code: str,
) -> list[tuple[WebSearchQueryResult, WebSearchPage]]:
    """Выдача запроса вместе со страницей каждой строки (для детальной запроса)."""
    stmt = (
        select(WebSearchQueryResult, WebSearchPage)
        .join(WebSearchPage, WebSearchQueryResult.page_code == WebSearchPage.code)
        .where(WebSearchQueryResult.query_code == query_code)
        .order_by(WebSearchQueryResult.rank, WebSearchQueryResult.id)
    )
    async with session_scope() as s:
        rows = (await s.execute(stmt)).all()
    return [(result, page) for result, page in rows]


__all__ = [
    "result_add",
    "results_for_query",
    "results_with_page_for_query",
]
