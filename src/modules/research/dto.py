"""DTO research — Row-контракты + составные read-представления.

**Префикс ``Agent`` = поверхность агента.** Что видит агент, в этом модуле управляется жёстко,
поэтому граница проведена именем: класс с префиксом ``Agent`` возвращается тулами MCP и больше
никем, всё остальное — контракты web-вьюера. Поиск по ``Agent`` в ``mcp/`` даёт всю агентскую
поверхность целиком. Где вопрос у обеих сторон один (строки списков), контракт общий и префикса
не несёт.

Интерфейсная деталь наследует агентскую и добавляет то, что нужно только человеку, — например
путь наверх (``research_code``/``research_title``): страница обязана вернуть его в родителя и при
прямом заходе по ссылке, когда истории переходов нет.

``*Row`` — тонкие зеркала строк (``from_attributes``). Даты сериализуются в SQL-формат ядровым
``DatetimeUTCStr`` — его ждёт фронт-парсер (``shared/utils/date.ts`` через Luxon ``fromSQL``, не
ISO с ``T``). Конверт списка — ядровый ``core.api.Paged``.
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


class AgentGroupCreated(BaseModel):
    """Возврат создания группы — только код."""

    model_config = ConfigDict(from_attributes=True)

    code: GroupCode


class AgentGroupScan(BaseModel):
    """Группа для MCP: одна карточка — ни оформления, ни позиции в списке.

    Как группа выглядит (``icon``/``color``) и где стоит (``sort``) — выбор человека в интерфейсе;
    для агента это лишние поля, поэтому поверхности разведены: MCP отдаёт этот набор,
    web-вьюер — ``GroupRow``.
    """

    model_config = ConfigDict(from_attributes=True)

    code: GroupCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class GroupRow(BaseModel):
    """Группа целиком для web-вьюера: тела у неё нет, скан и деталь — один набор полей."""

    model_config = ConfigDict(from_attributes=True)

    code: GroupCode
    title: str
    description: str = ""
    icon: str = ""
    color: str = ""
    sort: int
    updated_at: DatetimeUTCStr


class GroupListRow(GroupRow):
    """Строка списка групп для web-вьюера: карточка + сколько исследований в неё входит.

    Счётчик и дата работы — только тут: MCP отдаёт ``GroupRow`` без них — агенту они не нужны,
    а считать их на каждый вызов тула значило бы платить за то, что читает только интерфейс.

    ``research_updated_at`` — самое свежее обновление среди исследований группы, то есть «когда
    здесь последний раз работали»; ``None`` у пустой группы. Это НЕ ``updated_at`` самой группы:
    та меняется, когда человек правит имя или иконку.
    """

    research_count: int = 0
    research_updated_at: DatetimeUTCStr | None = None


class AgentResearchCreated(BaseModel):
    """Возврат создания исследования — только код (агент прислал остальное сам)."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode


class AgentResearchScan(BaseModel):
    """Скан research — код/заголовок/описание + группа (без дат/тела). Возврат research_update.

    ``group_code`` — ссылка (``None`` = не разложено), ``group_name`` — **вычисляемое** имя группы
    из join'а с ``research_group``: в самом исследовании названия группы нет и хранить его там
    было бы копией, разъезжающейся при переименовании. Пустая строка = группы нет.
    """

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""


class AgentResearchRow(BaseModel):
    """Строка research_list — скан-поля + группа + ``updated_at`` (без ``created_at``)."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""
    updated_at: DatetimeUTCStr


class AgentAreaScan(BaseModel):
    """Вложенная проекция области в research_get: код/заголовок/описание/updated_at."""

    model_config = ConfigDict(from_attributes=True)

    code: AreaCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class AgentNoteScan(BaseModel):
    """Вложенная проекция заметки в research_get: код/заголовок/описание/updated_at."""

    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class AgentResearchDetail(AgentResearchScan):
    """research_get: скан + тело + области и заметки (updated_at ↑) + даты (в конце)."""

    body: str = ""
    areas: list[AgentAreaScan] = []
    notes: list[AgentNoteScan] = []
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


class AgentSourceDocumentDetail(BaseModel):
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


class ResearchSourceDocumentDetail(AgentSourceDocumentDetail):
    """Источник для web-вьюера: агентская деталь + путь наверх — область и исследование.

    Цепочка полная, потому что источник лежит глубже всех: со страницы поднимаются и в область,
    из которой он найден, и сразу в исследование.
    """

    research_code: ResearchCode
    research_title: str = ""
    area_code: AreaCode
    area_title: str = ""


class AgentSkippedCode(BaseModel):
    """Код, по которому качать оказалось нечего, и почему именно — как его передали."""

    code: str
    reason: str


class AgentSourcesRefetched(BaseModel):
    """Итог повтора получения по нескольким кодам: что перекачано и что пропущено.

    Два списка вместо одного, потому что вопросов у агента тоже два: «что теперь читать»
    (``sources`` со свежим статусом) и «почему часть кодов ничего не дала» (``skipped``) —
    склеенные в один список, они заставляли бы отличать одно от другого по пустым полям.
    """

    sources: list["ResearchSourceDocumentRow"] = []
    skipped: list[AgentSkippedCode] = []


class AgentAreaCreated(BaseModel):
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


class AgentAreaDetail(BaseModel):
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


class AreaDetail(AgentAreaDetail):
    """Область для web-вьюера: агентская деталь + путь наверх, в исследование.

    Правило «``updated_at`` последним» тут уступает наследованию: добавленные наследником поля
    встают за унаследованными, и переставить их можно только повторив весь набор целиком.
    """

    research_code: ResearchCode
    research_title: str = ""


class AgentNoteCreated(BaseModel):
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


class AgentNoteDetail(BaseModel):
    """Заметка целиком: скан-слой + основное тело (markdown); ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    kind: str
    title: str
    description: str = ""
    body: str = ""
    updated_at: DatetimeUTCStr


class NoteDetail(AgentNoteDetail):
    """Заметка для web-вьюера: агентская деталь + путь наверх, в исследование."""

    research_code: ResearchCode
    research_title: str = ""


class ResearchListRow(BaseModel):
    """Строка списка исследований — группа (опознание + вид) + счётчики; ``updated_at`` последним.

    Вид группы (``group_icon``/``group_color``) едет вместе со строкой, а не добирается вторым
    запросом за списком групп: строка и так знает, к какой группе относится, и отдать её метку
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
    """Исследование + группа + тело + области, запросы и заметки; ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""
    # Вид группы едет с деталью по той же причине, что и со строкой списка: иначе страница
    # исследования ради одной плашки ходила бы за группой вторым запросом.
    group_icon: str = ""
    group_color: str = ""
    body: str = ""
    areas: list[AreaRow] = []
    queries: list[ResearchSourceQueryRow] = []
    notes: list[NoteRow] = []
    updated_at: DatetimeUTCStr


class SourceQueryDetail(ResearchSourceQueryRow):
    """Поиск + его источники (web-вьюер) + путь наверх: область и исследование.

    ``area_code`` уже несёт строка запроса — тут к нему добавляется только заголовок, которым
    область названа человеку.
    """

    research_code: ResearchCode
    research_title: str = ""
    area_title: str = ""
    documents: list[ResearchSourceDocumentRow] = []


class AgentBodyView(BaseModel):
    """Возврат body-редактора: код (с префиксом, эхо входа) + новое тело; ``updated_at`` последним."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    body: str = ""
    updated_at: DatetimeUTCStr


class AgentSkillRow(BaseModel):
    """Строка каталога навыков — имя, условие вызова, разделы; текста тут нет по замыслу."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str = ""
    sections: list[str] = []


class AgentSkill(BaseModel):
    """Прочитанный навык: текст целиком или один раздел (``section`` пуст у целого).

    ``sections`` едет и с телом раздела — иначе агент, ушедший вглубь, теряет список соседних
    веток и не знает, куда идти дальше.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str
    section: str = ""
    description: str = ""
    sections: list[str] = []
    text: str


class DeepSearchResult(BaseModel):
    """Коды сущностей, у которых запрос нашёлся **в теле**.

    Только коды: фронт уже держит сами строки — ему нужно лишь, какие из них подсветить.
    """

    areas: list[AreaCode] = []
    notes: list[NoteCode] = []
    sources: list[SourceDocumentCode] = []


class GroupSearchResult(BaseModel):
    """Группы, которые остаются на странице реестра при запросе.

    Только коды — по той же причине, что и у ``DeepSearchResult``: карточки со всем их
    содержимым фронт уже загрузил, ему нужно знать лишь, какие из них показать. ``ungrouped``
    — про псевдо-группу «Без группы», которой в БД нет и код которой поэтому не назвать.
    """

    codes: list[GroupCode] = []
    ungrouped: bool = False


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
    """Пара полей группы для контрактов исследования; нет группы → ``None`` + пустое имя."""
    return dict(
        group_code=group.code if group else None,
        group_name=group.title if group else "",
    )


def group_style_fields(group: "ResearchGroup | None") -> dict:
    """Как группу рисовать — иконка и цвет. Отдельно от ``group_fields``, потому что нужны они
    только интерфейсу: MCP-контракты делят с ним опознание группы (код и имя), но не её вид."""
    return dict(
        group_icon=group.icon if group else "",
        group_color=group.color if group else "",
    )


def agent_research_row(
    row: "Research", group: "ResearchGroup | None"
) -> AgentResearchRow:
    """Строка research_list: свои поля + имя группы из join'а."""
    return AgentResearchRow(
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


def agent_source_document_detail(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> AgentSourceDocumentDetail:
    """Деталь источника для агента: строка + тело материала (``web_search_page.body``)."""
    return AgentSourceDocumentDetail(
        **_source_document_fields(doc, page), body=page.body if page else None
    )


def source_document_detail(
    doc: "ResearchSourceDocument",
    page: "WebSearchPage | None",
    *,
    research_title: str = "",
    area_title: str = "",
) -> ResearchSourceDocumentDetail:
    """Деталь источника для web-вьюера: агентский набор + путь наверх.

    Заголовки родителей приходят разрешёнными снаружи (``crud/references``), а не достаются
    здесь: собирать DTO в обход сессии — правило модуля.
    """
    return ResearchSourceDocumentDetail(
        **_source_document_fields(doc, page),
        body=page.body if page else None,
        research_code=doc.research_code,
        research_title=research_title,
        area_code=doc.area_code,
        area_title=area_title,
    )


__all__ = [
    "AgentGroupCreated",
    "AgentGroupScan",
    "AgentResearchCreated",
    "AgentResearchScan",
    "AgentResearchRow",
    "AgentResearchDetail",
    "AgentAreaScan",
    "AgentNoteScan",
    "AgentAreaCreated",
    "AgentAreaDetail",
    "AgentNoteCreated",
    "AgentNoteDetail",
    "AgentSourceDocumentDetail",
    "AgentSkippedCode",
    "AgentSourcesRefetched",
    "AgentBodyView",
    "AgentSkill",
    "AgentSkillRow",
    "GroupRow",
    "GroupListRow",
    "ResearchRow",
    "AreaRow",
    "AreaDetail",
    "NoteRow",
    "NoteDetail",
    "ResearchSourceQueryRow",
    "ResearchSourceDocumentRow",
    "ResearchSourceDocumentDetail",
    "ResearchListRow",
    "ResearchDetail",
    "SourceQueryDetail",
    "ReferencesBody",
    "CodeLabel",
    "group_fields",
    "group_style_fields",
    "agent_research_row",
    "source_document_row",
    "agent_source_document_detail",
    "source_document_detail",
]
