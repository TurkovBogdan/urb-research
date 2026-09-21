"""DTO research — Row-контракты + составные read-представления.

**Префикс ``Agent`` = поверхность агента.** Что видит агент, в этом модуле управляется жёстко,
поэтому граница проведена именем: класс с префиксом ``Agent`` возвращается тулами MCP и больше
никем, всё остальное — контракты web-вьюера. Поиск по ``Agent`` в ``mcp/`` даёт всю агентскую
поверхность целиком. Граница сплошная: общих контрактов у поверхностей нет, даже там, где
наборы полей совпадают. Общий контракт разъезжается в одну сторону — поле,
добавленное ради колонки в таблице, молча начинает стоить агенту контекста в каждой сессии.

Докстринг агентского класса туда же: pydantic кладёт его в JSON-схему тула описанием, и агент
оплачивает его при каждом подключении. Поэтому пояснения агентских контрактов живут в
комментариях НАД классом, а не в докстринге.

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
    model_config = ConfigDict(from_attributes=True)

    code: GroupCode


# Оформление (``icon``/``color``) и позиция в списке (``sort``) — выбор человека в интерфейсе,
# поэтому поверхности разведены: MCP отдаёт этот набор, web-вьюер — ``GroupRow``.
class AgentGroupScan(BaseModel):
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
    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode


# ``group_name`` берётся join'ом, а не хранится в исследовании: хранимая копия разъезжалась бы
# с группой при переименовании.
class AgentResearchScan(BaseModel):
    """Скан research. ``group_code`` = ``None`` — не разложено; ``group_name`` производно от
    него (пустая строка = группы нет) и своей правки не имеет: переименовать группу можно
    только ``group_update``."""

    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""


class AgentResearchRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: ResearchCode
    title: str
    description: str = ""
    group_code: GroupCode | None = None
    group_name: str = ""
    updated_at: DatetimeUTCStr


# Даты правки в агентских сканах нет: списки приходят уже упорядоченными по ней, а сама она
# ничего не говорит — у заведённой и ни разу не тронутой области она равна дате заведения, так
# что отличить сделанное от несделанного по ней нельзя. Колонку с датой читает интерфейс.
class AgentAreaScan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: AreaCode
    title: str
    description: str = ""


# ``kind`` стоит наравне с названием: тип — это то, чем заметка является (вывод / гипотеза /
# открытый вопрос / …), и по нему агент решает, что с ней делать.
class AgentNoteScan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    kind: str
    title: str
    description: str = ""


class AgentResearchDetail(AgentResearchScan):
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


# Прогон поиска для агента: код, текст запроса и область, в которой он запущен. ``area_code``
# тут не путь наверх, а ключ группировки: ``query_search_list`` принимает и код исследования, и
# тогда в одном списке лежат прогоны разных областей — без него не увидеть, какая область
# обыскана слабее прочих, и пришлось бы звать список на каждую область отдельно.
class AgentSourceQueryScan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: SourceQueryCode
    area_code: AreaCode
    query: str


class ResearchSourceQueryRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: SourceQueryCode
    area_code: AreaCode
    query: str


# Источник, как его только что нашли или перекачали. ``status`` — весь его итог: ``pending``
# значит материал на месте и пора разбирать, ``error`` — качать снова (``sources_refetch``).
# Разбора у такого источника ещё нет, поэтому вердикта тут нет — его добавляет строка списка.
# ``title`` не украшение: код источника, вписанный в тело, читатель видит заголовком страницы,
# и текст вокруг ссылки агент пишет так, будто заголовок стоит на её месте.
class AgentSourceDocumentScan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: SourceDocumentCode
    status: str
    url: str | None = None
    title: str | None = None


# Строка списка источников: скан + вердикт разбора, вынесенный раньше. ``note``/``relevance`` —
# чем разбор помнит себя: вернувшись в область (или приняв её от другого агента), по ним видно,
# какой из оставленных источников ключевой, а какой отсеян и почему. Снипета поисковика
# (``summary``) тут нет намеренно: судить по нему запрещено, материал читается ``source_get``.
class AgentSourceDocumentRow(AgentSourceDocumentScan):
    note: str = ""
    relevance: int | None = None


# Итог ``source_review``: код источника и статус, в который его перевело решение. Оценка и
# заметка — вход того же вызова, а страница в разборе не участвует вовсе (``url``/``title``
# возвращались тут пустыми всегда). Эхо собственного ввода агент оплачивал бы на каждом
# разобранном источнике, а их в области десятки.
class AgentSourceDocumentReviewed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: SourceDocumentCode
    status: str


# Связочные коды (area/query/page), domain и код причины сбоя (``web_search_page.error``) сюда
# не идут: агент в контексте, страницу опознаёт по url, а решение о повторе принимает по
# ``status``. Причину сбоя человек смотрит в разделе страниц.
class ResearchSourceDocumentRow(BaseModel):
    """Источник без тела материала: статус, разбор и url/title страницы (тело — ``source_get``)."""

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
    """Источник + тело материала (``body``; ``None`` — страница не скачана)."""

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


class UnfetchedPageRow(BaseModel):
    """Страница без материала: чем она является, почему не дошла и сколько источников её ждут.

    ``code`` — код одного из этих источников: повтор заказывают по источнику, а чинится
    страница, и она снимает ``error`` со всех своих источников разом.
    """

    code: SourceDocumentCode
    url: str | None = None
    title: str | None = None
    error: str | None = None
    sources: int


class UnfetchedPlan(BaseModel):
    """Что предстоит перекачать на уровне и каким куском это просить.

    ``chunk_size`` считает движок контента (одна волна его батчей): резать работу на куски —
    дело заказчика повтора, но размер куска знает тот, кто качает.
    """

    pages: list[UnfetchedPageRow] = []
    sources_total: int = 0
    chunk_size: int = 1


class AgentSkippedCode(BaseModel):
    """Код, по которому качать оказалось нечего — любого из принятых типов, как его передали,
    — и причина."""

    code: str
    reason: str


# Два списка, а не один: у агента и вопроса два — что теперь читать и почему часть кодов
# ничего не дала. Склеенные, они заставляли бы отличать одно от другого по пустым полям.
class AgentSourcesRefetched(BaseModel):
    sources: list[AgentSourceDocumentScan] = []
    skipped: list[AgentSkippedCode] = []


class AgentAreaCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: AreaCode


class AreaRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: AreaCode
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class AgentAreaDetail(BaseModel):
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
    model_config = ConfigDict(from_attributes=True)

    code: NoteCode


class NoteRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: NoteCode
    kind: str
    title: str
    description: str = ""
    updated_at: DatetimeUTCStr


class AgentNoteDetail(BaseModel):
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

    ``created_at`` есть только здесь, а не в общей ``ResearchRow``: реестр показывает обе даты
    колонками и сортирует по каждой, а агенту дата заведения ни о чём не говорит.
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
    document_count: int = 0
    document_kept: int = 0
    document_filtered: int = 0
    document_error: int = 0
    created_at: DatetimeUTCStr
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


# Код в возвратах body-редактора — эхо входа, а не поле строки: тело правят у трёх типов сразу,
# и одного ``prefixed`` на все три нет; вернуть его голым значило бы отдать агенту код, который
# он не может передать обратно.

# Расписка ``body_set``: тело целиком написал сам агент, и эхо его же текста — чистая трата
# контекста. Длина же говорит то, чего агент не знает, — что сохранилось ровно написанное.
class AgentBodySet(BaseModel):
    code: str
    length: int


# Одна форма на оба режима ``body_replace``, а не объединение двух: агент должен знать, что ему
# вернут, до вызова. ``edits`` — по шву на каждое вхождение, в порядке документа; в режиме
# ``single`` это список из одного. Вхождения теснее окна отдают общий текст дважды: склейка
# стоила бы соответствия «шов на вхождение», по которому и сверяют ``replaced``.
class AgentBodyReplaced(BaseModel):
    code: str
    replaced: int
    edits: list[str] = []


# Возврат ``body_set_section`` — вырезанное, а не вписанное: границу раздела считает сервер по
# уровню заголовка, и непредсказуем для агента ровно размах выреза. Хвост блока и его полная
# длина отвечают на это прямо; шов вокруг нового текста выглядел бы одинаково и при вырезе вдвое
# шире нужного. ``stopped_at`` — заголовок, оборвавший блок (``None`` = тело кончилось).
class AgentBodySectionSet(BaseModel):
    code: str
    removed: str
    removed_length: int
    stopped_at: str | None = None


# Возврат ``body_add``: шов — единственное, что тут может пойти не так, ведь текст вклеивается
# дословно, без разделителя.
class AgentBodyAdded(BaseModel):
    code: str
    edit: str


class AgentSkillRow(BaseModel):
    """Строка каталога навыков: имя, условие вызова и разделы — без текста (его даёт ``skill_get``)."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str = ""
    sections: list[str] = []


# ``sections`` едет и с телом одного раздела: иначе агент, ушедший вглубь, теряет список
# соседних веток и не знает, куда идти дальше.
class AgentSkill(BaseModel):
    """Навык: текст целиком или один его раздел (``section`` пуст у целого)."""

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


def _source_scan_fields(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> dict:
    """Опознание источника: свой код и статус + чем он является — url/title из join'а страницы."""
    return dict(
        code=doc.code,
        status=doc.status,
        url=page.url if page else None,
        title=page.title if page else None,
    )


def _source_document_fields(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> dict:
    return dict(
        **_source_scan_fields(doc, page),
        summary=doc.summary,
        note=doc.note,
        relevance=doc.relevance,
        updated_at=doc.updated_at,
    )


def agent_source_document_scan(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> AgentSourceDocumentScan:
    """Только что найденный (или перекачанный) источник для агента — без вердикта разбора."""
    return AgentSourceDocumentScan(**_source_scan_fields(doc, page))


def agent_source_document_row(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> AgentSourceDocumentRow:
    """Строка списка источников для агента: скан + вердикт разбора."""
    return AgentSourceDocumentRow(
        **_source_scan_fields(doc, page), note=doc.note, relevance=doc.relevance
    )


def source_document_row(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None"
) -> ResearchSourceDocumentRow:
    """Собрать строку источника: свои поля + url/title из join'а страницы."""
    return ResearchSourceDocumentRow(**_source_document_fields(doc, page))


def unfetched_page_row(
    doc: "ResearchSourceDocument", page: "WebSearchPage | None", *, sources: int
) -> UnfetchedPageRow:
    """Строка плана повтора: страница глазами её источника + причина отказа из самой страницы."""
    return UnfetchedPageRow(
        code=doc.code,
        url=page.url if page else None,
        title=page.title if page else None,
        error=page.error if page else None,
        sources=sources,
    )


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
    "AgentSourceQueryScan",
    "AgentSourceDocumentScan",
    "AgentSourceDocumentRow",
    "AgentSourceDocumentReviewed",
    "AgentSourceDocumentDetail",
    "AgentSkippedCode",
    "AgentSourcesRefetched",
    "AgentBodySet",
    "AgentBodyReplaced",
    "AgentBodySectionSet",
    "AgentBodyAdded",
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
    "agent_source_document_scan",
    "agent_source_document_row",
    "source_document_row",
    "agent_source_document_detail",
    "source_document_detail",
]
