"""web_search: сохранение выдачи (searcher._store_results: page + result) + переходы страницы.

``_store_results`` создаёт страницы (в ``pending``) и строки выдачи и возвращает страницы,
оставшиеся в ``pending`` (их дотягивает сервис поиска: ``processing`` → ``done``/``error``).
"""

from __future__ import annotations

import pytest

from src.core.config import Config
from src.core.database import close_database, init_database
from src.modules.web_search.constants import (
    FETCH_STATUS_DONE,
    FETCH_STATUS_ERROR,
    FETCH_STATUS_PENDING,
)
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.crud.page import page_code
from src.modules.web_search.services.searcher import _store_results


async def _queue_query() -> str:
    row = await query_crud.query_create(
        search_engine="tavily", fetch_engine="tavily", query="q", params=None
    )
    return row.code


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    from src.core.database.runtime import Base
    import src.modules.web_search.models  # noqa: F401 — register tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.mark.db
async def test_store_attaches_pages_and_returns_pending(db):
    query_code = await _queue_query()
    results = [
        {"url": "http://example.com/a", "rank": 1, "score": 0.9, "summary": "S", "title": "A"},
        {"url": "https://example.com/b", "rank": 2},
    ]
    pending = await _store_results(query_code, results)

    assert {p.url for p in pending} == {"https://example.com/a", "https://example.com/b"}

    rows = await query_result_crud.results_for_query(query_code)
    assert len(rows) == 2
    assert {r.summary for r in rows} == {"S", None}

    page = await page_crud.page_get_by_code(page_code("http://example.com/a"))
    assert page is not None
    assert page.status == FETCH_STATUS_PENDING  # контент ещё не тянули
    assert page.url == "https://example.com/a"  # минимальная норм.: всегда https
    assert page.domain == "example.com"
    assert page.title == "A"  # заголовок из выдачи поиска — на странице


@pytest.mark.db
async def test_duplicate_url_in_one_query_dedups(db):
    query_code = await _queue_query()
    results = [{"url": "https://x.com/p", "rank": 1}, {"url": "https://x.com/p", "rank": 2}]
    pending = await _store_results(query_code, results)

    assert len(pending) == 1  # одна страница по дедупу
    rows = await query_result_crud.results_for_query(query_code)
    assert len(rows) == 1  # unique (query_code, page_code)


@pytest.mark.db
async def test_page_body_and_error_transitions(db):
    page = await page_crud.page_upsert("https://y.com/z")
    assert page.status == FETCH_STATUS_PENDING

    done = await page_crud.page_set_body(page.code, body="# hello")
    assert done is not None
    assert done.status == FETCH_STATUS_DONE
    assert done.body == "# hello"
    assert done.body_hash

    failing = await page_crud.page_upsert("https://y.com/err")
    erred = await page_crud.page_set_error(failing.code, error="timeout")
    assert erred is not None
    assert erred.status == FETCH_STATUS_ERROR
    assert erred.error == "timeout"
