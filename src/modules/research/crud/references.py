"""Разрешение ссылок-кодов в заголовки — для линкификации ``TYPE@hash`` в телах.

Тела исследования/области/заметки содержат кросс-ссылки на любые сущности
(``RESEARCH@`` / ``AREA@`` / ``NOTE@`` / ``QUERY@`` / ``SOURCE@`` / ``GROUP@``). Резолвер батчем
достаёт заголовок каждой (одним ``IN`` на затронутый тип) и возвращает
``{префиксный код → заголовок}`` — фронт подставляет заголовок в пилюлю ссылки.

У всех типов, кроме источника, заголовок лежит в собственной колонке — они разрешаются одним
общим запросом по таблице ``_TITLE_COLUMN``. Источник — исключение: своего заголовка у него нет,
он приезжает join'ом из ``web_search_page`` (см. ``models/source_document.py``).
"""

from __future__ import annotations

from sqlalchemy import select

from src.core.database import session_scope
from src.modules.research.codes import code_prefix, strip_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    GROUP_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.web_search.models.page import WebSearchPage

# Префикс → (модель, колонка-заголовок). У поиска собственного заголовка нет — его роль
# играет текст запроса.
_TITLE_COLUMN = {
    GROUP_CODE_PREFIX: (ResearchGroup, ResearchGroup.title),
    RESEARCH_CODE_PREFIX: (Research, Research.title),
    AREA_CODE_PREFIX: (ResearchArea, ResearchArea.title),
    NOTE_CODE_PREFIX: (ResearchNote, ResearchNote.title),
    SOURCE_QUERY_CODE_PREFIX: (ResearchSourceQuery, ResearchSourceQuery.query),
}


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
        for prefix, (model, title_column) in _TITLE_COLUMN.items():
            if prefix not in by_type:
                continue
            rows = await s.execute(
                select(model.code, title_column).where(model.code.in_(by_type[prefix]))
            )
            add(prefix, rows.all())

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
