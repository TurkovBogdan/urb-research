"""CRUD ``ResearchSourceQuery`` — источниковые запросы (research + area + web_search-прогон).

Каждая функция владеет сессией. Создаётся при запуске поиска (``query_search_run``): связывает
research + area с прогоном web_search. Поиск — **только ссылки**, тела/синтеза у запроса нет.
Код — голый 22-hex ``random_hash()`` (тип-префикс ``QUERY@`` — на границе, см. ``research.codes``).
"""

from __future__ import annotations

from sqlalchemy import delete, func, select

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery

def source_query_code() -> str:
    """Код источникового запроса — голый 22-hex ``random_hash`` (естественного ключа нет).

    Тип-префикс (``QUERY@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


async def source_query_create(
    *, research_code: str, area_code: str, search_code: str, query: str
) -> ResearchSourceQuery:
    async with session_scope() as s:
        row = ResearchSourceQuery(
            code=source_query_code(),
            research_code=research_code,
            area_code=area_code,
            search_code=search_code,
            query=query,
        )
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


async def source_query_get(code: str) -> ResearchSourceQuery | None:
    async with session_scope() as s:
        return await s.get(ResearchSourceQuery, code)


async def source_query_list_by_research(research_code: str) -> list[ResearchSourceQuery]:
    stmt = (
        select(ResearchSourceQuery)
        .where(ResearchSourceQuery.research_code == research_code)
        .order_by(ResearchSourceQuery.created_at.asc(), ResearchSourceQuery.code.asc())
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def source_query_list_by_area(area_code: str) -> list[ResearchSourceQuery]:
    stmt = (
        select(ResearchSourceQuery)
        .where(ResearchSourceQuery.area_code == area_code)
        .order_by(ResearchSourceQuery.created_at.asc(), ResearchSourceQuery.code.asc())
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def source_query_delete(code: str) -> bool:
    """Удалить прогон поиска. Каскад вручную: источники прогона → сам запрос.
    ``True`` — существовал и удалён."""
    async with session_scope() as s:
        row = await s.get(ResearchSourceQuery, code)
        if row is None:
            return False
        await s.execute(
            delete(ResearchSourceDocument).where(
                ResearchSourceDocument.query_code == code
            )
        )
        await s.delete(row)
    return True


async def source_query_count_by_research_codes(
    research_codes: list[str],
) -> dict[str, int]:
    """``research_code → число запросов`` одним GROUP BY (для списка исследований)."""
    if not research_codes:
        return {}
    stmt = (
        select(ResearchSourceQuery.research_code, func.count())
        .where(ResearchSourceQuery.research_code.in_(research_codes))
        .group_by(ResearchSourceQuery.research_code)
    )
    async with session_scope() as s:
        return {code: count for code, count in (await s.execute(stmt)).all()}


__all__ = [
    "source_query_code",
    "source_query_create",
    "source_query_get",
    "source_query_list_by_research",
    "source_query_list_by_area",
    "source_query_delete",
    "source_query_count_by_research_codes",
]
