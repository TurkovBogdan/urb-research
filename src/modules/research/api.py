"""HTTP read-API модуля ``research`` (mounted at /internal/research).

Только просмотр для web-вьюера: исследования (список + деталь с запросами) и
источниковый запрос (деталь с источниками + синтезом). Зона ``internal`` в чистом ядре
открыта (``allow_all``), guard не нужен. Данные пишет MCP-сервер, не эти ручки.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.core.api import ApiError, Paged
from src.modules.research.codes import strip_prefix
from src.modules.research.constants import DOC_FILTERED, DOC_KEPT, DOC_STATUSES
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import references as references_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.research.dto import (
    AreaDetail,
    AreaRow,
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
    source_document_detail,
    source_document_row,
)

router = APIRouter()

_MAX_PAGE_SIZE = 200


def _offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


@router.get("/researches")
async def list_researches(
    query: str | None = None,
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
) -> Paged[ResearchListRow]:
    rows = await research_crud.research_list_paged(
        query=query,
        sort_dir=sort_dir,
        offset=_offset(page, page_size),
        limit=page_size,
    )
    total = await research_crud.research_count(query=query)
    codes = [r.code for r in rows]
    area_counts = await area_crud.area_count_by_research_codes(codes)
    query_counts = await source_query_crud.source_query_count_by_research_codes(codes)
    doc_counts = await source_document_crud.source_document_status_counts_by_research_codes(codes)
    items = [
        ResearchListRow(
            **ResearchRow.model_validate(r).model_dump(),
            area_count=area_counts.get(r.code, 0),
            query_count=query_counts.get(r.code, 0),
            document_kept=doc_counts.get(r.code, {}).get(DOC_KEPT, 0),
            document_filtered=doc_counts.get(r.code, {}).get(DOC_FILTERED, 0),
        )
        for r in rows
    ]
    return Paged(items=items, total=total, page=page, page_size=page_size)


@router.get("/researches/{research_code}")
async def get_research(research_code: str) -> ResearchDetail:
    research_code = strip_prefix(research_code)
    research = await research_crud.research_get(research_code)
    if research is None:
        raise ApiError.not_found("Исследование не найдено")
    areas = await area_crud.area_list_by_research(research_code)
    queries = await source_query_crud.source_query_list_by_research(research_code)
    notes = await note_crud.note_list_by_research(research_code)
    return ResearchDetail(
        **ResearchRow.model_validate(research).model_dump(),
        body=research.body,
        areas=[AreaRow.model_validate(a) for a in areas],
        queries=[ResearchSourceQueryRow.model_validate(q) for q in queries],
        notes=[NoteRow.model_validate(n) for n in notes],
    )


@router.get("/areas/{area_code}")
async def get_area(area_code: str) -> AreaDetail:
    area_code = strip_prefix(area_code)
    area = await area_crud.area_get(area_code)
    if area is None:
        raise ApiError.not_found("Область не найдена")
    return AreaDetail.model_validate(area)


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


@router.get("/notes/{note_code}")
async def get_note(note_code: str) -> NoteDetail:
    note_code = strip_prefix(note_code)
    note = await note_crud.note_get(note_code)
    if note is None:
        raise ApiError.not_found("Заметка не найдена")
    return NoteDetail.model_validate(note)


__all__ = ["router"]
