"""DTO research — Row-контракты + составные read-представления.

``*Row`` — тонкие зеркала строк (``from_attributes``), общие для MCP и web-API.
Даты сериализуются в SQL-формат ядровым ``DatetimeUTCStr`` — его ждёт фронт-парсер
(``shared/utils/date.ts`` через Luxon ``fromSQL``, не ISO с ``T``). Конверт списка —
ядровый ``core.api.Paged``; ``*Detail``/``ListRow`` — составные под web-вьюер.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from src.core.utils.date import DatetimeUTCStr
from src.modules.research.codes import prefixed
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)

# Presentation-tagged code types: bare hash on the wire in, prefixed on the wire out.
ResearchCode = prefixed(RESEARCH_CODE_PREFIX)
AreaCode = prefixed(AREA_CODE_PREFIX)
NoteCode = prefixed(NOTE_CODE_PREFIX)
SourceQueryCode = prefixed(SOURCE_QUERY_CODE_PREFIX)
SourceDocumentCode = prefixed(SOURCE_DOCUMENT_CODE_PREFIX)


class ResearchCreated(BaseModel):
    """Возврат создания исследования — только код (агент прислал остальное сам)."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode


class ResearchScan(BaseModel):
    """Скан research — код/заголовок/описание (без дат/тела). Возврат research_update."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""


class ResearchListItem(BaseModel):
    """Строка research_list — код/заголовок/описание + ``updated_at`` (без ``created_at``)."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class AreaScan(BaseModel):
    """Вложенная проекция области в research_get: код/заголовок/описание/updated_at."""

    model_config = ConfigDict(from_attributes=True)

    code: AreaCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class NoteScan(BaseModel):
    """Вложенная проекция заметки в research_get: код/заголовок/описание/updated_at."""

    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class ResearchView(ResearchScan):
    """research_get: скан + тело + области и заметки (updated_at ↑) + даты (в конце)."""

    body: str = ""
    areas: list[AreaScan] = []
    notes: list[NoteScan] = []
    updated_at: DatetimeUTCStr


class ResearchRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class ResearchSourceQueryRow(BaseModel):
    """Строка поиска (query_search_list): код + к какой области + текст запроса."""

    model_config = ConfigDict(from_attributes=True)

    code: SourceQueryCode
    area_code: AreaCode
    query: str


class ResearchSourceDocumentRow(BaseModel):
    """Источник (скан): код + оценка + url/title из join'а страницы; ``updated_at`` последним.

    Связочные коды (area/query/page) и domain не отдаём — агент в контексте, страницу видит по url.
    """

    model_config = ConfigDict(from_attributes=True)

    code: SourceDocumentCode
    status: str
    url: str | None = None
    title: str | None = None
    summary: str = ""
    note: str = ""
    relevance: int | None = None
    updated_at: DatetimeUTCStr


class ResearchSourceDocumentDetail(BaseModel):
    """Источник + тело материала (``web_search_page.body`` через join); ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: SourceDocumentCode
    status: str
    url: str | None = None
    title: str | None = None
    summary: str = ""
    note: str = ""
    relevance: int | None = None
    body: str | None = None
    updated_at: DatetimeUTCStr


class AreaCreated(BaseModel):
    """Возврат создания области — только код."""

    model_config = ConfigDict(from_attributes=True)

    code: AreaCode


class AreaRow(BaseModel):
    """Скан-слой области: код + заголовок + краткое «что это» (для списка N областей)."""

    model_config = ConfigDict(from_attributes=True)

    code: AreaCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class AreaDetail(BaseModel):
    """Область целиком: скан-слой + бриф (objective/scope/expectations) + body; ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: AreaCode
    title: str
    description: str = ""
    objective: str = ""
    scope: str = ""
    expectations: str = ""
    body: str = ""
    updated_at: DatetimeUTCStr


class NoteCreated(BaseModel):
    """Возврат создания заметки — только код."""

    model_config = ConfigDict(from_attributes=True)

    code: NoteCode


class NoteRow(BaseModel):
    """Скан-слой заметки: код + тип + заголовок + краткое «что это» (для списка)."""

    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    kind: str
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class NoteDetail(BaseModel):
    """Заметка целиком: скан-слой + основное тело (markdown); ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    kind: str
    title: str
    description: str = ""
    body: str = ""
    updated_at: DatetimeUTCStr


class ResearchListRow(BaseModel):
    """Строка списка исследований — со счётчиками (области/поиски/принято/отсеяно); ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    area_count: int = 0
    query_count: int = 0
    document_kept: int = 0
    document_filtered: int = 0
    updated_at: DatetimeUTCStr


class ResearchDetail(BaseModel):
    """Исследование + тело + области, запросы и заметки; ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    body: str = ""
    areas: list[AreaRow] = []
    queries: list[ResearchSourceQueryRow] = []
    notes: list[NoteRow] = []
    updated_at: DatetimeUTCStr


class SourceQueryDetail(ResearchSourceQueryRow):
    """Поиск + его источники (web-вьюер)."""

    documents: list[ResearchSourceDocumentRow] = []


class BodyView(BaseModel):
    """Возврат body-редактора: код (с префиксом, эхо входа) + новое тело; ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    body: str = ""
    updated_at: DatetimeUTCStr


class ReferencesBody(BaseModel):
    """Тело запроса разрешения ссылок-кодов в теле — набор ``TYPE@hash`` (или голых)."""

    codes: list[str] = []


class CodeLabel(BaseModel):
    """Разрешение ссылки: **префиксный** код (совпадает с ключом на фронте) + заголовок сущности."""

    code: str
    title: str | None = None


if TYPE_CHECKING:
    from src.modules.research.models.source_document import ResearchSourceDocument
    from src.modules.web_search.models.page import WebSearchPage


def _source_document_fields(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> dict:
    return dict(
        code=doc.code,
        status=doc.status,
        url=page.url if page else None,
        title=page.title if page else None,
        summary=doc.summary,
        note=doc.note,
        relevance=doc.relevance,
        updated_at=doc.updated_at,
    )


def source_document_row(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> ResearchSourceDocumentRow:
    """Собрать строку источника: свои поля + url/domain/title из join'а страницы."""
    return ResearchSourceDocumentRow(**_source_document_fields(doc, page))


def source_document_detail(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> ResearchSourceDocumentDetail:
    """Деталь источника: строка + тело материала (``web_search_page.body``)."""
    return ResearchSourceDocumentDetail(
        **_source_document_fields(doc, page), body=page.body if page else None
    )


__all__ = [
    "ResearchCreated",
    "ResearchScan",
    "ResearchListItem",
    "AreaScan",
    "NoteScan",
    "ResearchView",
    "ResearchRow",
    "AreaCreated",
    "AreaRow",
    "AreaDetail",
    "NoteCreated",
    "NoteRow",
    "NoteDetail",
    "ResearchSourceQueryRow",
    "ResearchSourceDocumentRow",
    "ResearchSourceDocumentDetail",
    "ResearchListRow",
    "ResearchDetail",
    "SourceQueryDetail",
    "BodyView",
    "ReferencesBody",
    "CodeLabel",
    "source_document_row",
    "source_document_detail",
]
