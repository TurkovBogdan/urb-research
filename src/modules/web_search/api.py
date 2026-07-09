"""HTTP-API модуля ``web_search`` (mounted at /internal/web-search).

Просмотр: запросы (``web_search_query``) и страницы (``web_search_page``) — списки
(пагинация ``page``/``page_size`` + фильтры текст/статус/движок|домен) и детальные
(запрос с его выдачей; страница с контентом). Запуск: ``POST /queries`` ставит поиск в
фон (**fire-and-forget** — клиент не ждёт, прогресс виден поллингом списка); ``GET /engines``
отдаёт доступные движки по ролям для формы создания. Зона ``internal`` в чистом ядре открыта
(``allow_all``), поэтому guard не нужен.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.core.api import ApiError, Paged
from src.modules.web_search import settings
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.models.page import PageDetail, PageRow
from src.modules.web_search.models.query import QueryDetail, QueryRow
from src.modules.web_search.models.query_result import QueryResultView
from src.modules.web_search.services.searcher import Searcher

router = APIRouter()

_MAX_PAGE_SIZE = 200


class CreateQueryBody(BaseModel):
    """Тело ``POST /queries``: текст запроса + опциональные движки/лимит (None → дефолт настроек)."""

    query: str = Field(min_length=1, max_length=2000)
    search_engine: str | None = None
    fetch_engine: str | None = None
    max_results: int | None = Field(default=None, ge=1, le=50)


class EnginesInfo(BaseModel):
    """Доступные движки по ролям (коды включённых в ``core_connectors``) + дефолты для формы."""

    search: list[str]
    fetch: list[str]
    search_default: str
    fetch_default: str


def _offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


@router.get("/queries")
async def list_queries(
    query: str | None = None,
    status: str | None = None,
    search_engine: str | None = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
) -> Paged[QueryRow]:
    rows = await query_crud.query_list(
        query=query,
        status=status,
        search_engine=search_engine,
        sort_by=sort_by,
        sort_dir=sort_dir,
        offset=_offset(page, page_size),
        limit=page_size,
    )
    total = await query_crud.query_count(query=query, status=status, search_engine=search_engine)
    return Paged(
        items=[QueryRow.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/queries", status_code=202)
async def create_query(body: CreateQueryBody) -> QueryRow:
    """Fire-and-forget: поставить поиск в фон, вернуть ``pending``-запрос сразу (клиент не ждёт)."""
    try:
        row = await Searcher.submit(
            body.query,
            search_engine=body.search_engine,
            fetch_engine=body.fetch_engine,
            max_results=body.max_results,
        )
    except KeyError:
        raise ApiError.bad_request("Неизвестный движок") from None
    return QueryRow.model_validate(row)


@router.get("/engines")
async def list_engines() -> EnginesInfo:
    """Доступные движки по ролям (включённые в ``core_connectors``) + дефолты для формы создания."""
    return EnginesInfo(
        search=Searcher.search_engines(),
        fetch=Searcher.fetch_engines(),
        search_default=settings.search_engine(),
        fetch_default=settings.fetch_engine(),
    )


@router.get("/queries/{code}")
async def get_query(code: str) -> QueryDetail:
    row = await query_crud.query_get(code)
    if row is None:
        raise ApiError.not_found("Запрос не найден")
    pairs = await query_result_crud.results_with_page_for_query(code)
    results = [
        QueryResultView(
            page_code=result.page_code,
            rank=result.rank,
            score=result.score,
            summary=result.summary,
            meta=result.meta,
            page_url=page.url,
            page_title=page.title,
            page_domain=page.domain,
            page_status=page.status,
            page_fetched_at=page.fetched_at,
        )
        for result, page in pairs
    ]
    return QueryDetail(**QueryRow.model_validate(row).model_dump(), results=results)


@router.get("/pages")
async def list_pages(
    query: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=_MAX_PAGE_SIZE),
) -> Paged[PageRow]:
    rows = await page_crud.page_list(
        query=query,
        status=status,
        domain=domain,
        sort_by=sort_by,
        sort_dir=sort_dir,
        offset=_offset(page, page_size),
        limit=page_size,
    )
    total = await page_crud.page_count(query=query, status=status, domain=domain)
    return Paged(
        items=[PageRow.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/pages/{code}")
async def get_page(code: str) -> PageDetail:
    page = await page_crud.page_get_by_code(code)
    if page is None:
        raise ApiError.not_found("Страница не найдена")
    return PageDetail.model_validate(page)


__all__ = ["router"]
