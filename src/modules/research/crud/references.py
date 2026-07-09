"""Разрешение ссылок-кодов в заголовки — для линкификации ``TYPE@hash`` в телах.

Тела исследования/области/заметки содержат кросс-ссылки на любые сущности
(``RESEARCH@`` / ``AREA@`` / ``NOTE@`` / ``QUERY@`` / ``SOURCE@``). Резолвер батчем
достаёт заголовок каждой (одним ``IN`` на затронутый тип) и возвращает
``{префиксный код → заголовок}`` — фронт подставляет заголовок в пилюлю ссылки.
"""

from __future__ import annotations

from sqlalchemy import select

from src.core.database import session_scope
from src.modules.research.codes import code_prefix, strip_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.web_search.models.page import WebSearchPage


async def resolve_labels(codes: list[str]) -> dict[str, str]:
    """``[префиксный код] → заголовок`` для набора кодов любых типов (пустой заголовок опущен)."""
    by_type: dict[str, list[str]] = {}
    for code in codes:
        by_type.setdefault(code_prefix(code), []).append(strip_prefix(code))
    labels: dict[str, str] = {}

    def add(prefix: str, rows) -> None:
        for code, title in rows:
            if title:
                labels[f"{prefix}@{code}"] = title

    async with session_scope() as s:
        if RESEARCH_CODE_PREFIX in by_type:
            rows = await s.execute(
                select(Research.code, Research.title).where(
                    Research.code.in_(by_type[RESEARCH_CODE_PREFIX])
                )
            )
            add(RESEARCH_CODE_PREFIX, rows.all())
        if AREA_CODE_PREFIX in by_type:
            rows = await s.execute(
                select(ResearchArea.code, ResearchArea.title).where(
                    ResearchArea.code.in_(by_type[AREA_CODE_PREFIX])
                )
            )
            add(AREA_CODE_PREFIX, rows.all())
        if NOTE_CODE_PREFIX in by_type:
            rows = await s.execute(
                select(ResearchNote.code, ResearchNote.title).where(
                    ResearchNote.code.in_(by_type[NOTE_CODE_PREFIX])
                )
            )
            add(NOTE_CODE_PREFIX, rows.all())
        if SOURCE_QUERY_CODE_PREFIX in by_type:
            rows = await s.execute(
                select(ResearchSourceQuery.code, ResearchSourceQuery.query).where(
                    ResearchSourceQuery.code.in_(by_type[SOURCE_QUERY_CODE_PREFIX])
                )
            )
            add(SOURCE_QUERY_CODE_PREFIX, rows.all())
        if SOURCE_DOCUMENT_CODE_PREFIX in by_type:
            rows = await s.execute(
                select(ResearchSourceDocument.code, WebSearchPage.title)
                .outerjoin(
                    WebSearchPage, ResearchSourceDocument.page_code == WebSearchPage.code
                )
                .where(
                    ResearchSourceDocument.code.in_(by_type[SOURCE_DOCUMENT_CODE_PREFIX])
                )
            )
            add(SOURCE_DOCUMENT_CODE_PREFIX, rows.all())

    return labels


__all__ = ["resolve_labels"]
