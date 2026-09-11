"""research CRUD источников: возврат в очередь после повтора получения + пустые входы.

``source_document_revive_by_pages`` — мостик из web_search: правит по ``page_code``, а не по
области, потому что одна страница дедуплицирована на несколько исследований.
"""

from __future__ import annotations

import pytest

from src.modules.research.constants import DOC_ERROR, DOC_FILTERED, DOC_KEPT, DOC_PENDING
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.web_search.crud import page as page_crud

pytestmark = pytest.mark.db


async def _source_on(page_code: str, *, status: str) -> str:
    """Источник заданного статуса на указанной странице (со своим исследованием/областью)."""
    research = await research_crud.research_create(title="R")
    area = await area_crud.area_create(research_code=research.code, title="A")
    query = await source_query_crud.source_query_create(
        research_code=research.code, area_code=area.code, search_code="s", query="q"
    )
    doc = await source_document_crud.source_document_create(
        research_code=research.code,
        area_code=area.code,
        query_code=query.code,
        page_code=page_code,
        status=status,
    )
    return doc.code


async def _fetched_page(url: str) -> str:
    page = await page_crud.page_upsert(url)
    await page_crud.page_set_body(page.code, body="# body")
    return page.code


async def _status_of(code: str) -> str:
    found = await source_document_crud.source_document_get(code)
    assert found is not None
    return found[0].status


async def test_revive_clears_error_on_every_source_of_a_shared_page(db):
    page = await _fetched_page("https://shared.example/doc")
    first = await _source_on(page, status=DOC_ERROR)
    second = await _source_on(page, status=DOC_ERROR)

    await source_document_crud.source_document_revive_by_pages([page])

    assert await _status_of(first) == DOC_PENDING
    assert await _status_of(second) == DOC_PENDING


async def test_revive_leaves_reviewed_sources_alone(db):
    page = await _fetched_page("https://shared.example/reviewed")
    kept = await _source_on(page, status=DOC_KEPT)
    filtered = await _source_on(page, status=DOC_FILTERED)

    await source_document_crud.source_document_revive_by_pages([page])

    assert await _status_of(kept) == DOC_KEPT
    assert await _status_of(filtered) == DOC_FILTERED


async def test_revive_keeps_error_while_the_page_has_no_body(db):
    dead = await page_crud.page_upsert("https://shared.example/dead")
    await page_crud.page_set_error(dead.code, error="ConnectError")
    source = await _source_on(dead.code, status=DOC_ERROR)

    await source_document_crud.source_document_revive_by_pages([dead.code])

    assert await _status_of(source) == DOC_ERROR


async def test_empty_input_touches_nothing(db):
    assert await source_document_crud.source_document_list_by_codes([]) == []
    assert await page_crud.pages_by_codes([]) == []
    await source_document_crud.source_document_revive_by_pages([])
