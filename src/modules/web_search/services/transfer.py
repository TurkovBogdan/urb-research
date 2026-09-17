"""Шов переноса: выгрузка строк web_search в архив исследования и приём их обратно.

Формат переноса принадлежит модулю research, а таблицы — этому модулю: страница и прогон
поиска живут здесь, и класть их готовыми строками (с чужим кодом, временем и статусом) вправе
только их владелец. Поэтому research отдаёт сюда разобранные строки и забирает отсюда те, что
нужно выгрузить, а прямой записи в чужие таблицы в проекте по-прежнему нет.

Обычный CRUD для переноса не годится: ``page_upsert`` заводит страницу в ``pending`` по url,
а переносу нужно положить её ровно такой, какой она уехала, — с материалом, статусом и
отметкой времени получения.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.core.database import session_scope, write_scope
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.models.query_result import WebSearchQueryResult


def _insert_for(session):
    """Диалектный ``INSERT`` с поддержкой ``ON CONFLICT`` (sqlite и postgres расходятся типом)."""
    dialect = session.bind.dialect.name if session.bind else "postgresql"
    return sqlite_insert if dialect == "sqlite" else pg_insert


async def pages_by_codes(codes: list[str]) -> list[WebSearchPage]:
    """Страницы по кодам — то, что уже есть в этой базе (порядок не гарантирован)."""
    if not codes:
        return []
    async with session_scope() as s:
        rows = await s.execute(select(WebSearchPage).where(WebSearchPage.code.in_(codes)))
        return list(rows.scalars().all())


async def searches_by_codes(codes: list[str]) -> list[WebSearchQuery]:
    """Прогоны поиска по кодам."""
    if not codes:
        return []
    async with session_scope() as s:
        rows = await s.execute(select(WebSearchQuery).where(WebSearchQuery.code.in_(codes)))
        return list(rows.scalars().all())


async def results_for_searches(codes: list[str]) -> list[WebSearchQueryResult]:
    """Строки выдачи перечисленных прогонов, в порядке ранга."""
    if not codes:
        return []
    stmt = (
        select(WebSearchQueryResult)
        .where(WebSearchQueryResult.query_code.in_(codes))
        .order_by(WebSearchQueryResult.query_code, WebSearchQueryResult.rank, WebSearchQueryResult.id)
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def result_pairs_for_searches(codes: list[str]) -> set[tuple[str, str]]:
    """Естественные ключи выдачи ``(query_code, page_code)`` — по ним строка выдачи и опознаётся."""
    if not codes:
        return set()
    stmt = select(WebSearchQueryResult.query_code, WebSearchQueryResult.page_code).where(
        WebSearchQueryResult.query_code.in_(codes)
    )
    async with session_scope() as s:
        return {(query_code, page_code) for query_code, page_code in (await s.execute(stmt)).all()}


async def pages_insert(rows: list[dict[str, Any]]) -> int:
    """Вставить страницы как есть; уже существующий код пропускается молча.

    Возврат — сколько строк отдано на вставку, а не сколько легло: конфликт по коду означает,
    что страница с этим url в базе уже есть, и это законный исход слияния.
    """
    if not rows:
        return 0
    async with write_scope() as s:
        stmt = _insert_for(s)(WebSearchPage).values(rows).on_conflict_do_nothing(
            index_elements=["code"]
        )
        await s.execute(stmt)
    return len(rows)


async def page_fill_material(
    code: str,
    *,
    body: str | None,
    body_hash: str | None,
    status: str,
    fetch_engine: str | None,
    fetched_at: Any,
    error: str | None,
) -> None:
    """Дописать материал в существующую страницу (пустую или упавшую) из архива."""
    async with write_scope() as s:
        await s.execute(
            update(WebSearchPage)
            .where(WebSearchPage.code == code)
            .values(
                body=body,
                body_hash=body_hash,
                status=status,
                fetch_engine=fetch_engine,
                fetched_at=fetched_at,
                error=error,
            )
        )


async def searches_insert(rows: list[dict[str, Any]]) -> int:
    """Вставить прогоны поиска как есть; существующий код пропускается молча."""
    if not rows:
        return 0
    async with write_scope() as s:
        stmt = _insert_for(s)(WebSearchQuery).values(rows).on_conflict_do_nothing(
            index_elements=["code"]
        )
        await s.execute(stmt)
    return len(rows)


async def search_replace(code: str, values: dict[str, Any]) -> None:
    """Переписать поля прогона поиска значениями из архива (код не трогаем)."""
    if not values:
        return
    async with write_scope() as s:
        await s.execute(update(WebSearchQuery).where(WebSearchQuery.code == code).values(**values))


async def results_insert(rows: list[dict[str, Any]]) -> int:
    """Вставить строки выдачи; дубль по ``(query_code, page_code)`` пропускается молча.

    Суррогатный ``id`` не переносится — его выдаёт принимающая база, а строка опознаётся
    естественным ключом.
    """
    if not rows:
        return 0
    async with write_scope() as s:
        stmt = _insert_for(s)(WebSearchQueryResult).values(rows).on_conflict_do_nothing(
            index_elements=["query_code", "page_code"]
        )
        await s.execute(stmt)
    return len(rows)


__all__ = [
    "pages_by_codes",
    "searches_by_codes",
    "results_for_searches",
    "result_pairs_for_searches",
    "pages_insert",
    "page_fill_material",
    "searches_insert",
    "search_replace",
    "results_insert",
]
