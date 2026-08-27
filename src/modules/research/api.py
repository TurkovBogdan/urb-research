"""HTTP-API модуля ``research`` (mounted at /internal/research).

Содержимое ресёрча (исследования, области, поиски, источники, заметки) **пишет MCP-сервер**,
не эти ручки — пользователю остаются просмотр, раскладка по группам, переименование и удаление.

- **Группы** — полностью пользовательские: группа это раскладка человека, а не результат работы
  агента, поэтому у неё полный набор write-ручек плюс узкая ``PUT /researches/{code}/group``
  (меняет только привязку, не открывая правку самого исследования).
- **Переименование** (``PUT .../title`` на исследовании / области / заметке) — за пользователем:
  название это то, как человек находит артефакт у себя в списке, и оно не обязано совпадать
  с формулировкой агента. Ручки нарочно узкие, как ``.../group``: одно поле, остальной текст
  (описание, бриф, тело) остаётся за MCP.
- **Удаление** (``DELETE`` на исследовании / области / поиске / заметке) — тоже за пользователем:
  выбросить наработанное это решение человека, а не агента. Ручки зеркалят одноимённые
  MCP-тулы и тот же ручной каскад в CRUD (sqlite FK-каскад выключен). Отдельный источник
  (``SOURCE@``) не удаляется ни тут, ни в MCP: источник — строка выдачи поиска, его судьба
  решается ревью (``kept``/``filtered``) или удалением всего прогона.

- **Повтор получения материала** (``POST .../documents/refetch`` на исследовании / области,
  ``POST /source-documents/{code}/refetch`` на одном источнике) — зеркало MCP-тула
  ``sources_refetch``: содержимое не пишет, а добирает то, что не скачалось. По уровню чинятся
  источники без материала (``error``), по одиночному коду — он сам в любом статусе, и его разбор
  при этом сбрасывается.

Зона ``internal`` в чистом ядре открыта (``allow_all``), guard не нужен.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field, StringConstraints

from src.core.api import ApiError, Paged
from src.modules.research.codes import strip_prefix
from src.modules.research.constants import (
    AREA_TITLE_MAX,
    DOC_ERROR,
    DOC_FILTERED,
    DOC_KEPT,
    DOC_STATUSES,
    GROUP_COLOR_MAX,
    GROUP_DESCRIPTION_MAX,
    GROUP_ICON_MAX,
    GROUP_RESEARCHES_ACTIONS,
    GROUP_RESEARCHES_DETACH,
    GROUP_RESEARCHES_MOVE,
    GROUP_TITLE_MAX,
    NOTE_TITLE_MAX,
    RESEARCH_TITLE_MAX,
)
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import group as group_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import references as references_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.research.dto import (
    AreaDetail,
    AreaRow,
    DeepSearchResult,
    GroupListRow,
    GroupRow,
    GroupSearchResult,
    NoteDetail,
    NoteRow,
    ResearchDetail,
    ResearchListRow,
    ResearchRow,
    ResearchSourceDocumentDetail,
    ResearchSourceDocumentRow,
    ResearchSourceQueryRow,
    CodeLabel,
    ReferencesBody,
    SourceQueryDetail,
    group_fields,
    group_style_fields,
    source_document_detail,
    source_document_row,
)
from src.modules.research.services.refetch import refetch_sources
from src.modules.research.services.search import search_bodies, search_groups, search_researches

router = APIRouter()

_MAX_PAGE_SIZE = 200
# Значение ``group_code`` в списке, означающее «только не разложенные по группам».
# Строка, а не ``None``: ``None`` в query-параметре неотличим от «параметр не передан».
_UNGROUPED = ""


class GroupBody(BaseModel):
    """Тело создания/правки группы.

    Пустая иконка — «не выбрана», фронт рисует запасную; пустой цвет — «не выбран», фронт красит
    акцентом. Имена не сверяются с палитрами (``icons.py`` / ``colors.py``) — по той же причине,
    по которой их не проверяет БД: рисовать умеет только фронт, и он же переживёт незнакомое имя.
    """

    title: str = Field(min_length=1, max_length=GROUP_TITLE_MAX)
    description: str = Field(default="", max_length=GROUP_DESCRIPTION_MAX)
    icon: str = Field(default="", max_length=GROUP_ICON_MAX)
    color: str = Field(default="", max_length=GROUP_COLOR_MAX)
    sort: int | None = None


class ResearchGroupBody(BaseModel):
    """Тело ``PUT /researches/{code}/group``: код группы либо ``None`` — убрать из группы."""

    group_code: str | None = None


# Строгий из потолков трёх переименовываемых сущностей: тело одно на все три ручки, и оно
# не вправе пропустить название длиннее, чем примет самая узкая колонка.
_TITLE_MAX = min(RESEARCH_TITLE_MAX, AREA_TITLE_MAX, NOTE_TITLE_MAX)


class TitleBody(BaseModel):
    """Тело переименования. Обрамляющие пробелы срезаются ДО проверки длины, поэтому имя из
    одних пробелов отвергается наравне с пустым: артефакт без имени неразличим в списке,
    а «стереть название» — не сценарий."""

    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=_TITLE_MAX)
    ]


def _offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


async def _require_group(code: str) -> None:
    if await group_crud.group_get(code) is None:
        raise ApiError.not_found("Группа не найдена")


@router.get("/groups")
async def list_groups(
    sort_by: str = Query(
        group_crud.GROUP_SORT_BY_DEFAULT,
        description=f"Поле сортировки: {', '.join(group_crud.GROUP_SORT_BY_COLUMNS)}",
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
) -> list[GroupListRow]:
    """Полки в порядке показа + счётчик и дата работы на карточке."""
    rows = await group_crud.group_list(sort_by=sort_by, sort_dir=sort_dir)
    codes = [row.code for row in rows]
    counts = await research_crud.research_count_by_group_codes(codes)
    worked_at = await research_crud.research_updated_at_by_group_codes(codes)
    return [
        GroupListRow(
            **GroupRow.model_validate(row).model_dump(),
            research_count=counts.get(row.code, 0),
            research_updated_at=worked_at.get(row.code),
        )
        for row in rows
    ]


@router.get("/groups/search")
async def search_groups_by_text(
    q: str = Query(""),
    in_researches: bool = Query(
        True, description="Искать и в исследованиях группы; false — только текст самих групп"
    ),
) -> GroupSearchResult:
    """Какие группы оставить на странице реестра: ищем в группе и во всём тексте её исследований.

    Объявлена ДО ``/groups/{group_code}``: FastAPI сопоставляет маршруты в порядке объявления,
    и ниже по файлу ``search`` уехал бы в код группы.

    Ищет по написанному человеком и агентом — группа, исследование, его зоны (включая бриф) и
    заметки; материал источников не смотрим. Пустой запрос ничего не сужает.
    """
    matches = await search_groups(q, in_researches=in_researches)
    return GroupSearchResult(codes=matches.codes, ungrouped=matches.ungrouped)


@router.post("/groups", status_code=201)
async def create_group(payload: GroupBody) -> GroupRow:
    row = await group_crud.group_create(
        title=payload.title,
        description=payload.description,
        icon=payload.icon,
        color=payload.color,
        sort=payload.sort,
    )
    return GroupRow.model_validate(row)


@router.get("/groups/{group_code}")
async def get_group(group_code: str) -> GroupRow:
    row = await group_crud.group_get(strip_prefix(group_code))
    if row is None:
        raise ApiError.not_found("Группа не найдена")
    return GroupRow.model_validate(row)


@router.put("/groups/{group_code}")
async def update_group(group_code: str, payload: GroupBody) -> GroupRow:
    """Полная замена карточки группы: тело несёт все поля, ``sort`` опускается — остаётся прежним."""
    row = await group_crud.group_update(
        strip_prefix(group_code),
        title=payload.title,
        description=payload.description,
        icon=payload.icon,
        color=payload.color,
        sort=payload.sort,
    )
    if row is None:
        raise ApiError.not_found("Группа не найдена")
    return GroupRow.model_validate(row)


@router.delete("/groups/{group_code}", status_code=204)
async def delete_group(
    group_code: str,
    researches: str = Query(
        GROUP_RESEARCHES_DETACH,
        pattern=f"^({'|'.join(GROUP_RESEARCHES_ACTIONS)})$",
        description="Судьба исследований группы: снять / перевесить / удалить",
    ),
    move_to: str | None = Query(None, description="Куда перевесить при researches=move"),
) -> Response:
    """Удалить группу. По умолчанию исследования переживают её — становятся не разложенными."""
    group_code = strip_prefix(group_code)
    move_to = strip_prefix(move_to)
    if researches == GROUP_RESEARCHES_MOVE:
        if not move_to:
            raise ApiError.bad_request("Не указана группа, куда переместить исследования")
        if move_to == group_code:
            raise ApiError.bad_request("Нельзя переместить исследования в удаляемую группу")
        await _require_group(move_to)
    if not await group_crud.group_delete(
        group_code, researches=researches, move_to=move_to
    ):
        raise ApiError.not_found("Группа не найдена")
    return Response(status_code=204)


@router.get("/researches")
async def list_researches(
    query: str | None = Query(
        None,
        description=(
            "Поиск по тексту исследования: название, описание, тело, а также тела его зон "
            "(включая бриф) и заметок — глубину задаёт in_bodies. Источники не ищутся."
        ),
    ),
    in_bodies: bool = Query(
        True, description="Искать и в телах исследований; false — только названия и описания"
    ),
    group_code: str | None = Query(
        None, description="Полка: код группы, пустая строка — только не разложенные"
    ),
    sort_by: str = Query(
        research_crud.RESEARCH_SORT_DEFAULT,
        description=f"Поле сортировки: {', '.join(research_crud.RESEARCH_SORT_COLUMNS)}",
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
) -> Paged[ResearchListRow]:
    group_code = strip_prefix(group_code)
    if group_code:
        await _require_group(group_code)
    # Поиск идёт по тексту, а не по колонке заголовка, поэтому отрабатывает до SQL и приезжает
    # сюда списком кодов; группу, сортировку и страницу накладывает уже запрос.
    codes = (
        await search_researches(query, in_bodies=in_bodies) if query and query.strip() else None
    )
    rows = await research_crud.research_list_paged(
        codes=codes,
        sort_by=sort_by,
        sort_dir=sort_dir,
        offset=_offset(page, page_size),
        limit=page_size,
        group_code=group_code,
    )
    total = await research_crud.research_count(codes=codes, group_code=group_code)
    codes = [r.code for r, _ in rows]
    area_counts = await area_crud.area_count_by_research_codes(codes)
    query_counts = await source_query_crud.source_query_count_by_research_codes(codes)
    doc_counts = await source_document_crud.source_document_status_counts_by_research_codes(codes)
    items = [
        ResearchListRow(
            **ResearchRow.model_validate(r).model_dump(),
            **group_fields(group),
            **group_style_fields(group),
            area_count=area_counts.get(r.code, 0),
            query_count=query_counts.get(r.code, 0),
            document_kept=doc_counts.get(r.code, {}).get(DOC_KEPT, 0),
            document_filtered=doc_counts.get(r.code, {}).get(DOC_FILTERED, 0),
        )
        for r, group in rows
    ]
    return Paged(items=items, total=total, page=page, page_size=page_size)


@router.get("/researches/{research_code}")
async def get_research(research_code: str) -> ResearchDetail:
    research_code = strip_prefix(research_code)
    found = await research_crud.research_get_with_group(research_code)
    if found is None:
        raise ApiError.not_found("Исследование не найдено")
    research, group = found
    areas = await area_crud.area_list_by_research(research_code)
    queries = await source_query_crud.source_query_list_by_research(research_code)
    notes = await note_crud.note_list_by_research(research_code)
    return ResearchDetail(
        **ResearchRow.model_validate(research).model_dump(),
        **group_fields(group),
        **group_style_fields(group),
        body=research.body,
        areas=[AreaRow.model_validate(a) for a in areas],
        queries=[ResearchSourceQueryRow.model_validate(q) for q in queries],
        notes=[NoteRow.model_validate(n) for n in notes],
    )


@router.get("/researches/{research_code}/search")
async def search_research(research_code: str, q: str = Query("")) -> DeepSearchResult:
    """Глубокий поиск: где запрос встречается **в телах** зон, заметок и в материале источников.

    Дополняет мгновенный поиск фронта, а не заменяет его: тот ищет по скан-слою (названия,
    описания, разбор источника), который у него уже есть, а тела сюда не доходят — материал
    одного исследования доходит до полутора десятков мегабайт. Ответ — только коды.
    """
    research_code = strip_prefix(research_code)
    if await research_crud.research_get(research_code) is None:
        raise ApiError.not_found("Исследование не найдено")
    matches = await search_bodies(research_code, q)
    return DeepSearchResult(
        areas=matches.areas, notes=matches.notes, sources=matches.sources
    )


@router.put("/researches/{research_code}/title")
async def rename_research(research_code: str, payload: TitleBody) -> ResearchDetail:
    """Переименовать исследование."""
    research_code = strip_prefix(research_code)
    if await research_crud.research_update(research_code, title=payload.title) is None:
        raise ApiError.not_found("Исследование не найдено")
    return await get_research(research_code)


@router.put("/researches/{research_code}/group")
async def set_research_group(
    research_code: str, payload: ResearchGroupBody
) -> ResearchDetail:
    """Положить исследование в группу или убрать из неё (``group_code: null``).

    Единственная write-ручка по исследованию: меняет только привязку — содержимое ресёрча
    по-прежнему пишет MCP-сервер.
    """
    research_code = strip_prefix(research_code)
    group_code = strip_prefix(payload.group_code) or _UNGROUPED
    if group_code:
        await _require_group(group_code)
    row = await research_crud.research_update(research_code, group_code=group_code)
    if row is None:
        raise ApiError.not_found("Исследование не найдено")
    return await get_research(research_code)


@router.delete("/researches/{research_code}", status_code=204)
async def delete_research(research_code: str) -> Response:
    """Удалить исследование со всем, что под ним: области, поиски, источники, заметки."""
    if not await research_crud.research_delete(strip_prefix(research_code)):
        raise ApiError.not_found("Исследование не найдено")
    return Response(status_code=204)


@router.get("/areas/{area_code}")
async def get_area(area_code: str) -> AreaDetail:
    area_code = strip_prefix(area_code)
    area = await area_crud.area_get(area_code)
    if area is None:
        raise ApiError.not_found("Область не найдена")
    return AreaDetail.model_validate(area)


@router.put("/areas/{area_code}/title")
async def rename_area(area_code: str, payload: TitleBody) -> AreaDetail:
    """Переименовать область."""
    area = await area_crud.area_update(strip_prefix(area_code), title=payload.title)
    if area is None:
        raise ApiError.not_found("Область не найдена")
    return AreaDetail.model_validate(area)


@router.delete("/areas/{area_code}", status_code=204)
async def delete_area(area_code: str) -> Response:
    """Удалить область вместе с её поисками и источниками. Исследование остаётся."""
    if not await area_crud.area_delete(strip_prefix(area_code)):
        raise ApiError.not_found("Область не найдена")
    return Response(status_code=204)


def _validated_status(status: str | None) -> str | None:
    if status is not None and status not in DOC_STATUSES:
        raise ApiError.bad_request("Неизвестный статус документа")
    return status


@router.get("/areas/{area_code}/queries")
async def list_area_queries(area_code: str) -> list[ResearchSourceQueryRow]:
    area_code = strip_prefix(area_code)
    rows = await source_query_crud.source_query_list_by_area(area_code)
    return [ResearchSourceQueryRow.model_validate(r) for r in rows]


@router.get("/areas/{area_code}/documents")
async def list_area_documents(
    area_code: str, status: str | None = None
) -> list[ResearchSourceDocumentRow]:
    area_code = strip_prefix(area_code)
    rows = await source_document_crud.source_document_list_by_area(
        area_code, status=_validated_status(status)
    )
    return [source_document_row(doc, page) for doc, page in rows]


@router.get("/researches/{research_code}/documents")
async def list_research_documents(
    research_code: str, status: str | None = None
) -> list[ResearchSourceDocumentRow]:
    research_code = strip_prefix(research_code)
    rows = await source_document_crud.source_document_list_by_research(
        research_code, status=_validated_status(status)
    )
    return [source_document_row(doc, page) for doc, page in rows]


async def _refetched_rows(
    documents: list[source_document_crud.SourceDocumentWithPage],
) -> list[ResearchSourceDocumentRow]:
    """Перекачать материал источников; выключенный движок контента — отказ, а не пустой прогон."""
    try:
        rows = await refetch_sources(documents)
    except RuntimeError:
        raise ApiError.bad_request(
            "Движок получения контента выключен в настройках"
        ) from None
    return [source_document_row(doc, page) for doc, page in rows]


@router.post("/areas/{area_code}/documents/refetch")
async def refetch_area_documents(area_code: str) -> list[ResearchSourceDocumentRow]:
    """Перекачать материал источников области, у которых он не получен (``error``)."""
    broken = await source_document_crud.source_document_list_by_area(
        strip_prefix(area_code), status=DOC_ERROR
    )
    return await _refetched_rows(broken)


@router.post("/researches/{research_code}/documents/refetch")
async def refetch_research_documents(
    research_code: str,
) -> list[ResearchSourceDocumentRow]:
    """Перекачать материал источников исследования, у которых он не получен (``error``)."""
    broken = await source_document_crud.source_document_list_by_research(
        strip_prefix(research_code), status=DOC_ERROR
    )
    return await _refetched_rows(broken)


@router.get("/source-queries/{query_code}")
async def get_source_query(query_code: str) -> SourceQueryDetail:
    query_code = strip_prefix(query_code)
    query_row = await source_query_crud.source_query_get(query_code)
    if query_row is None:
        raise ApiError.not_found("Запрос не найден")
    documents = await source_document_crud.source_document_list_by_query(query_code)
    return SourceQueryDetail(
        **ResearchSourceQueryRow.model_validate(query_row).model_dump(),
        documents=[source_document_row(doc, page) for doc, page in documents],
    )


@router.delete("/source-queries/{query_code}", status_code=204)
async def delete_source_query(query_code: str) -> Response:
    """Удалить прогон поиска вместе с его источниками. Страницы web_search остаются — они
    общие для всех исследований (источник ссылается на страницу, а не владеет ею)."""
    if not await source_query_crud.source_query_delete(strip_prefix(query_code)):
        raise ApiError.not_found("Запрос не найден")
    return Response(status_code=204)


@router.post("/references")
async def resolve_references(payload: ReferencesBody) -> list[CodeLabel]:
    """Разрешить ссылки-коды из тела (``TYPE@hash``) в заголовки сущностей (батч)."""
    labels = await references_crud.resolve_labels(payload.codes)
    return [CodeLabel(code=code, title=title) for code, title in labels.items()]


@router.get("/source-documents/{document_code}")
async def get_source_document(document_code: str) -> ResearchSourceDocumentDetail:
    document_code = strip_prefix(document_code)
    result = await source_document_crud.source_document_get(document_code)
    if result is None:
        raise ApiError.not_found("Источник не найден")
    doc, page = result
    return source_document_detail(doc, page)


@router.post("/source-documents/{document_code}/refetch")
async def refetch_source_document(document_code: str) -> ResearchSourceDocumentRow:
    """Перекачать материал одного источника — в любом статусе, в том числе разобранного.

    Разбор при этом снимается: вердикт был вынесен по прежнему материалу, а страницу скачали
    заново (оценка и заметка остаются). Одна страница дедуплицирована между исследованиями,
    поэтому её соседи-источники тоже перестают числиться сломанными.
    """
    found = await source_document_crud.source_document_get(strip_prefix(document_code))
    if found is None:
        raise ApiError.not_found("Источник не найден")
    rows = await _refetched_rows([found])
    return rows[0]


@router.get("/notes/{note_code}")
async def get_note(note_code: str) -> NoteDetail:
    note_code = strip_prefix(note_code)
    note = await note_crud.note_get(note_code)
    if note is None:
        raise ApiError.not_found("Заметка не найдена")
    return NoteDetail.model_validate(note)


@router.put("/notes/{note_code}/title")
async def rename_note(note_code: str, payload: TitleBody) -> NoteDetail:
    """Переименовать заметку."""
    note = await note_crud.note_update(strip_prefix(note_code), title=payload.title)
    if note is None:
        raise ApiError.not_found("Заметка не найдена")
    return NoteDetail.model_validate(note)


@router.delete("/notes/{note_code}", status_code=204)
async def delete_note(note_code: str) -> Response:
    """Удалить заметку. Ниже неё ничего нет — каскада не требуется."""
    if not await note_crud.note_delete(strip_prefix(note_code)):
        raise ApiError.not_found("Заметка не найдена")
    return Response(status_code=204)


__all__ = ["router"]
