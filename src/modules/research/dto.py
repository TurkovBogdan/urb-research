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
    GROUP_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)

# Presentation-tagged code types: bare hash on the wire in, prefixed on the wire out.
GroupCode = prefixed(GROUP_CODE_PREFIX)
ResearchCode = prefixed(RESEARCH_CODE_PREFIX)
AreaCode = prefixed(AREA_CODE_PREFIX)
NoteCode = prefixed(NOTE_CODE_PREFIX)
SourceQueryCode = prefixed(SOURCE_QUERY_CODE_PREFIX)
SourceDocumentCode = prefixed(SOURCE_DOCUMENT_CODE_PREFIX)


class GroupCreated(BaseModel):
    """Возврат создания группы — только код."""

    model_config = ConfigDict(from_attributes=True)

    code: GroupCode


class GroupScan(BaseModel):
    """Группа для MCP: одна карточка — ни оформления, ни позиции в списке.

    Как полка выглядит (``icon``/``color``) и где лежит (``sort``) — выбор человека в интерфейсе;
    для агента это лишние поля, поэтому поверхности разведены: MCP отдаёт этот набор,
    web-вьюер — ``GroupRow``.
    """

    model_config = ConfigDict(from_attributes=True)

    code: GroupCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class GroupRow(BaseModel):
    """Группа целиком для web-вьюера: у полки нет тела, скан и деталь — один набор полей."""

    model_config = ConfigDict(from_attributes=True)

    code: GroupCode
    title: str
    description: str = ""
    icon: str = ""
    color: str = ""
    sort: int
    updated_at: DatetimeUTCStr


class GroupListRow(GroupRow):
    """Строка списка полок для web-вьюера: карточка + сколько исследований на ней лежит.

    Счётчик только тут: MCP отдаёт ``GroupRow`` без него — агенту он не нужен, а считать его
    на каждый вызов тула значило бы платить за то, что читает только интерфейс.
    """

    research_count: int = 0


class ResearchCreated(BaseModel):
    """Возврат создания исследования — только код (агент прислал остальное сам)."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode


class ResearchScan(BaseModel):
    """Скан research — код/заголовок/описание + полка (без дат/тела). Возврат research_update.

    ``group_code`` — ссылка (``None`` = не разложено), ``group_name`` — **вычисляемое** имя полки
    из join'а с ``research_group``: в самом исследовании названия группы нет и хранить его там
    было бы копией, разъезжающейся при переименовании. Пустая строка = группы нет.
    """

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""


class ResearchListItem(BaseModel):
    """Строка research_list — скан-поля + полка + ``updated_at`` (без ``created_at``)."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""
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
    Код причины сбоя (``web_search_page.error``) тоже не отдаём: решение о повторе не агентское,
    ему достаточно ``status`` — материала нет. Причина видна человеку в разделе страниц.
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


class SkippedCode(BaseModel):
    """Код, по которому качать оказалось нечего, и почему именно — как его передали."""

    code: str
    reason: str


class SourcesRefetched(BaseModel):
    """Итог повтора получения по нескольким кодам: что перекачано и что пропущено.

    Два списка вместо одного, потому что вопросов у агента тоже два: «что теперь читать»
    (``sources`` со свежим статусом) и «почему часть кодов ничего не дала» (``skipped``) —
    склеенные в один список, они заставляли бы отличать одно от другого по пустым полям.
    """

    sources: list["ResearchSourceDocumentRow"] = []
    skipped: list[SkippedCode] = []


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
    """Строка списка исследований — полка (опознание + вид) + счётчики; ``updated_at`` последним.

    Вид полки (``group_icon``/``group_color``) едет вместе со строкой, а не добирается вторым
    запросом за списком полок: строка и так знает, к какой полке относится, и отдать её метку
    сразу дешевле, чем заставлять каждого потребителя списка держать ещё и справочник.
    """

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""
    group_icon: str = ""
    group_color: str = ""
    area_count: int = 0
    query_count: int = 0
    document_kept: int = 0
    document_filtered: int = 0
    updated_at: DatetimeUTCStr


class ResearchDetail(BaseModel):
    """Исследование + полка + тело + области, запросы и заметки; ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""
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


class DeepSearchResult(BaseModel):
    """Коды сущностей, у которых запрос нашёлся **в теле**.

    Только коды: фронт уже держит сами строки — ему нужно лишь, какие из них подсветить.
    """

    areas: list[AreaCode] = []
    notes: list[NoteCode] = []
    sources: list[SourceDocumentCode] = []


class ReferencesBody(BaseModel):
    """Тело запроса разрешения ссылок-кодов в теле — набор ``TYPE@hash`` (или голых)."""

    codes: list[str] = []


class CodeLabel(BaseModel):
    """Разрешение ссылки: **префиксный** код (совпадает с ключом на фронте) + заголовок сущности."""

    code: str
    title: str | None = None


if TYPE_CHECKING:
    from src.modules.research.models.group import ResearchGroup
    from src.modules.research.models.research import Research
    from src.modules.research.models.source_document import ResearchSourceDocument
    from src.modules.web_search.models.page import WebSearchPage


def group_fields(group: "ResearchGroup | None") -> dict:
    """Пара полей полки для контрактов исследования; нет группы → ``None`` + пустое имя."""
    return dict(
        group_code=group.code if group else None,
        group_name=group.title if group else "",
    )


def group_style_fields(group: "ResearchGroup | None") -> dict:
    """Как полку рисовать — иконка и цвет. Отдельно от ``group_fields``, потому что нужны они
    только интерфейсу: MCP-контракты делят с ним опознание полки (код и имя), но не её вид."""
    return dict(
        group_icon=group.icon if group else "",
        group_color=group.color if group else "",
    )


def research_list_item(
    row: "Research", group: "ResearchGroup | None"
) -> ResearchListItem:
    """Строка research_list: свои поля + имя полки из join'а группы."""
    return ResearchListItem(
        code=row.code,
        title=row.title,
        description=row.description,
        **group_fields(group),
        updated_at=row.updated_at,
    )


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
    "GroupCreated",
    "GroupRow",
    "GroupListRow",
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
    "SkippedCode",
    "SourcesRefetched",
    "ResearchListRow",
    "ResearchDetail",
    "SourceQueryDetail",
    "BodyView",
    "ReferencesBody",
    "CodeLabel",
    "group_fields",
    "group_style_fields",
    "research_list_item",
    "source_document_row",
    "source_document_detail",
]
