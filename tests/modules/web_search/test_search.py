"""web_search: синхронный ``Searcher.search()`` — поиск ссылок + получение контента (без сети).

Движок-заглушка умеет обе роли (поиск + контент), регистрируется в обоих реестрах;
дефолтные геттеры ``Searcher._default_search_engine``/``_default_fetch_engine`` монкипатчатся
на её код. Проверяем терминалы запроса (``done``/``error``) и страниц (``done``/``error``),
а также что поиск даёт ссылки, а контент дотягивается отдельно.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.core.config import Config
from src.core.database import close_database, init_database
from src.modules.web_search.constants import (
    FETCH_STATUS_DONE,
    FETCH_STATUS_ERROR,
    SEARCH_STATUS_DONE,
    SEARCH_STATUS_ERROR,
    SEARCH_STATUS_PENDING,
)
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.crud.page import page_code
from src.modules.web_search.providers import base, registry
from src.modules.web_search.providers.base import FetchEngine, SearchEngine
from src.modules.web_search.providers.request import SearchRequest
from src.modules.web_search.services import searcher
from src.modules.web_search.services.searcher import Searcher


class _StubProvider(SearchEngine, FetchEngine):
    code = "stub"
    enabled_field = "tavily_gateway_enabled"  # доступность берётся из core_connectors

    def __init__(self, *, results=None, error=None, pages=None, pages_per_request=20) -> None:
        self._results = results or []
        self._error = error
        self._pages = pages or {}
        self.pages_per_request = pages_per_request

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        if self._error is not None:
            raise self._error
        return self._results

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        out: dict[str, str | None] = {}
        for url in urls:
            value = self._pages.get(url)
            if isinstance(value, Exception):
                raise value
            out[url] = value
        return out


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


@pytest.fixture
def use_stub(monkeypatch):
    def _install(stub: _StubProvider) -> _StubProvider:
        registry.search_engines.register(stub)
        registry.fetch_engines.register(stub)
        monkeypatch.setattr(Searcher, "_default_search_engine", lambda: "stub")
        monkeypatch.setattr(Searcher, "_default_fetch_engine", lambda: "stub")
        return stub

    return _install


@pytest.mark.db
async def test_search_records_both_providers(db, use_stub):
    use_stub(_StubProvider(results=[]))
    query = await Searcher.search("q")
    assert query.search_engine == "stub"
    assert query.fetch_engine == "stub"


@pytest.mark.db
async def test_search_fetches_content_for_links(db, use_stub):
    use_stub(
        _StubProvider(
            results=[{"url": "https://ok.com/a", "rank": 1, "score": 0.9}],
            pages={"https://ok.com/a": "# fetched body"},
            pages_per_request=1,
        )
    )

    query = await Searcher.search("q")

    assert query.status == SEARCH_STATUS_DONE
    assert query.finished_at is not None
    page = await page_crud.page_get_by_code(page_code("https://ok.com/a"))
    assert page.status == FETCH_STATUS_DONE
    assert page.body == "# fetched body"
    assert page.fetch_engine == "stub"  # движок контента снят на попытке фетча


@pytest.mark.db
async def test_search_no_results_marks_done(db, use_stub):
    use_stub(_StubProvider(results=[]))

    query = await Searcher.search("q")

    assert query.status == SEARCH_STATUS_DONE  # empty убран: пустая выдача — тоже done
    assert query.finished_at is not None


@pytest.mark.db
async def test_search_engine_failure_marks_error_without_raising(db, use_stub):
    use_stub(_StubProvider(error=RuntimeError("boom")))

    query = await Searcher.search("q")

    assert query.status == SEARCH_STATUS_ERROR
    assert query.error == "RuntimeError"
    assert query.finished_at is not None


@pytest.mark.db
async def test_search_disabled_provider_errors_before_network(db, use_stub, monkeypatch):
    called = False

    async def _fail(request):
        nonlocal called
        called = True
        return []

    stub = use_stub(_StubProvider(results=[]))
    monkeypatch.setattr(stub, "search", _fail)
    monkeypatch.setattr(base, "service_enabled", lambda field: False)  # шлюз выключен

    query = await Searcher.search("q")

    assert query.status == SEARCH_STATUS_ERROR
    assert query.error == "search_engine_disabled"
    assert called is False  # движок не звался — отвалились до сети


@pytest.mark.db
async def test_search_page_fetch_empty_and_error(db, use_stub):
    use_stub(
        _StubProvider(
            results=[
                {"url": "https://empty.com/a", "rank": 1},
                {"url": "https://err.com/b", "rank": 2},
            ],
            pages={
                "https://empty.com/a": None,  # контент не пришёл → page error
                "https://err.com/b": RuntimeError("boom"),  # фетч упал → page error
            },
            pages_per_request=1,
        )
    )

    query = await Searcher.search("q")

    assert query.status == SEARCH_STATUS_DONE  # ссылки есть → запрос done, даже при сбоях страниц
    empty_page = await page_crud.page_get_by_code(page_code("https://empty.com/a"))
    err_page = await page_crud.page_get_by_code(page_code("https://err.com/b"))
    assert empty_page.status == FETCH_STATUS_ERROR
    assert err_page.status == FETCH_STATUS_ERROR
    assert empty_page.fetch_engine == "stub"  # движок снят и при ошибке страницы
    assert err_page.fetch_engine == "stub"


@pytest.mark.db
async def test_search_records_results_with_ranks(db, use_stub):
    use_stub(
        _StubProvider(
            results=[
                {"url": "https://a.com", "rank": 1, "score": 0.9},
                {"url": "https://b.com", "rank": 2},
            ],
            pages={"https://a.com": "# a", "https://b.com": "# b"},
            pages_per_request=20,
        )
    )

    query = await Searcher.search("q")

    rows = await query_result_crud.results_for_query(query.code)
    assert [r.page_code for r in rows] == [
        page_code("https://a.com"),
        page_code("https://b.com"),
    ]
    assert rows[0].score == 0.9


@pytest.mark.db
async def test_submit_returns_pending_then_runs_in_background(db, use_stub):
    use_stub(
        _StubProvider(
            results=[{"url": "https://ok.com/a", "rank": 1}],
            pages={"https://ok.com/a": "# body"},
            pages_per_request=1,
        )
    )

    row = await Searcher.submit("q")
    assert row.status == SEARCH_STATUS_PENDING  # вернулась сразу, до прогона
    assert row.search_engine == "stub" and row.fetch_engine == "stub"

    await asyncio.gather(*list(searcher._BACKGROUND_TASKS))  # дождаться фонового прогона

    done = await query_crud.query_get(row.code)
    assert done.status == SEARCH_STATUS_DONE
    page = await page_crud.page_get_by_code(page_code("https://ok.com/a"))
    assert page.status == FETCH_STATUS_DONE
    assert page.body == "# body"
