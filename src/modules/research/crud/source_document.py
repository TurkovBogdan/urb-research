"""CRUD ``ResearchSourceDocument`` — источник: ссылка + оценка. Сессия на функцию.

**Read'ы джойнят ``web_search_page``** по ``page_code`` (url/domain/title/body — там, не копируем;
research = потребитель модуля сырых данных). Возвращают кортежи ``(doc, page|None)`` —
``page`` может быть ``None`` (страница ещё/уже отсутствует). Локальные поля источника
(status/relevance/summary/note) правятся сеттерами.
"""

from __future__ import annotations

from sqlalchemy import func, select, update

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.constants import DOC_ERROR, DOC_PENDING
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.web_search.constants import FETCH_STATUS_DONE
from src.modules.web_search.models.page import WebSearchPage

SourceDocumentWithPage = tuple[ResearchSourceDocument, WebSearchPage | None]


def source_document_code() -> str:
    """Код источника — голый 22-hex ``random_hash``.

    Тип-префикс (``SOURCE@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


async def source_document_create(
    *,
    research_code: str,
    area_code: str,
    query_code: str,
    page_code: str,
    summary: str | None = None,
    status: str = DOC_PENDING,
) -> ResearchSourceDocument:
    async with session_scope() as s:
        row = ResearchSourceDocument(
            code=source_document_code(),
            research_code=research_code,
            area_code=area_code,
            query_code=query_code,
            page_code=page_code,
            summary=summary or "",
            status=status,
        )
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


def _with_page():
    return select(ResearchSourceDocument, WebSearchPage).outerjoin(
        WebSearchPage, ResearchSourceDocument.page_code == WebSearchPage.code
    )


async def source_document_get(code: str) -> SourceDocumentWithPage | None:
    stmt = _with_page().where(ResearchSourceDocument.code == code)
    async with session_scope() as s:
        row = (await s.execute(stmt)).first()
    return (row[0], row[1]) if row else None


async def _list(condition, status: str | None) -> list[SourceDocumentWithPage]:
    """Источники по условию уровня + join страницы, сорт **по логике запуска** (``created_at`` ↑
    = прогоны в порядке запуска), опц. фильтр ``status``."""
    stmt = _with_page().where(condition)
    if status is not None:
        stmt = stmt.where(ResearchSourceDocument.status == status)
    stmt = stmt.order_by(
        ResearchSourceDocument.created_at.asc(), ResearchSourceDocument.code.asc()
    )
    async with session_scope() as s:
        rows = (await s.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def source_document_list_by_query(
    query_code: str, *, status: str | None = None
) -> list[SourceDocumentWithPage]:
    return await _list(ResearchSourceDocument.query_code == query_code, status)


async def source_document_list_by_area(
    area_code: str, *, status: str | None = None
) -> list[SourceDocumentWithPage]:
    return await _list(ResearchSourceDocument.area_code == area_code, status)


async def source_document_list_by_research(
    research_code: str, *, status: str | None = None
) -> list[SourceDocumentWithPage]:
    return await _list(ResearchSourceDocument.research_code == research_code, status)


async def source_document_list_by_codes(codes: list[str]) -> list[SourceDocumentWithPage]:
    """Перечитать источники по их кодам (порядок запуска) — снимок после повтора получения."""
    if not codes:
        return []
    return await _list(ResearchSourceDocument.code.in_(codes), None)


async def source_document_revive_by_pages(page_codes: list[str]) -> None:
    """Вернуть в очередь на разбор источники, чьи страницы наконец скачались.

    Правится по ``page_code``, а не по области: одна страница дедуплицирована на несколько
    исследований, и ожившая страница обязана снять ``error`` со **всех** своих источников —
    иначе в соседнем исследовании останется ``error`` при живом теле. Разобранные (``kept`` /
    ``filtered``) не трогаем: их оценка уже вынесена по материалу.
    """
    if not page_codes:
        return
    fetched = select(WebSearchPage.code).where(
        WebSearchPage.code.in_(page_codes), WebSearchPage.status == FETCH_STATUS_DONE
    )
    stmt = (
        update(ResearchSourceDocument)
        .where(
            ResearchSourceDocument.page_code.in_(fetched),
            ResearchSourceDocument.status == DOC_ERROR,
        )
        .values(status=DOC_PENDING)
    )
    async with session_scope() as s:
        await s.execute(stmt)


async def source_document_reset_by_codes(codes: list[str]) -> None:
    """Привести статус перекачанных источников к состоянию их страницы: материал пришёл →
    ``pending`` (снова в очереди на разбор), не пришёл → ``error``.

    В отличие от ``source_document_revive_by_pages`` правит **именно запрошенные** источники и
    снимает с них вердикт (``kept`` / ``filtered``): он был вынесен по прежнему материалу, а
    страницу только что скачали заново. Оценка и заметка остаются — прежний разбор читается
    дальше.
    """
    if not codes:
        return
    fetched = select(WebSearchPage.code).where(WebSearchPage.status == FETCH_STATUS_DONE)
    requested = ResearchSourceDocument.code.in_(codes)
    async with session_scope() as s:
        await s.execute(
            update(ResearchSourceDocument)
            .where(requested, ResearchSourceDocument.page_code.in_(fetched))
            .values(status=DOC_PENDING)
        )
        await s.execute(
            update(ResearchSourceDocument)
            .where(requested, ResearchSourceDocument.page_code.not_in(fetched))
            .values(status=DOC_ERROR)
        )


async def source_material_by_research(research_code: str) -> list[tuple[str, str | None]]:
    """``(code источника, тело страницы)`` по всему исследованию — сырьё для глубокого поиска.

    Материал живёт в ``web_search_page``, у источника только ссылка на неё; берём две колонки,
    а не ORM-пары — на большом исследовании это полтора десятка мегабайт текста.
    """
    stmt = (
        select(ResearchSourceDocument.code, WebSearchPage.body)
        .join(WebSearchPage, ResearchSourceDocument.page_code == WebSearchPage.code)
        .where(ResearchSourceDocument.research_code == research_code)
    )
    async with session_scope() as s:
        return [(code, body) for code, body in (await s.execute(stmt)).all()]


async def source_document_status_counts_by_research_codes(
    research_codes: list[str],
) -> dict[str, dict[str, int]]:
    """``research_code → {status: число документов}`` одним GROUP BY (для списка исследований)."""
    if not research_codes:
        return {}
    stmt = (
        select(
            ResearchSourceDocument.research_code,
            ResearchSourceDocument.status,
            func.count(),
        )
        .where(ResearchSourceDocument.research_code.in_(research_codes))
        .group_by(ResearchSourceDocument.research_code, ResearchSourceDocument.status)
    )
    counts: dict[str, dict[str, int]] = {}
    async with session_scope() as s:
        for research_code, status, count in (await s.execute(stmt)).all():
            counts.setdefault(research_code, {})[status] = count
    return counts


async def _set(code: str, values: dict) -> ResearchSourceDocument | None:
    stmt = (
        update(ResearchSourceDocument)
        .where(ResearchSourceDocument.code == code)
        .values(**values)
        .returning(ResearchSourceDocument)
    )
    async with session_scope() as s:
        return (await s.execute(stmt)).scalars().first()


async def source_document_review(
    code: str, *, status: str, relevance: int, note: str | None = None
) -> ResearchSourceDocument | None:
    """Разбор источника одним апдейтом: решение (``status`` kept/filtered) + рейтинг
    (``relevance`` 1–10) + опц. причина (``note``)."""
    values: dict = {"status": status, "relevance": relevance}
    if note is not None:
        values["note"] = note
    return await _set(code, values)


__all__ = [
    "source_document_code",
    "source_document_create",
    "source_document_get",
    "source_document_list_by_query",
    "source_document_list_by_area",
    "source_document_list_by_research",
    "source_document_list_by_codes",
    "source_document_revive_by_pages",
    "source_document_reset_by_codes",
    "source_material_by_research",
    "source_document_status_counts_by_research_codes",
    "source_document_review",
    "SourceDocumentWithPage",
]
