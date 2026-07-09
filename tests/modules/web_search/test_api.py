"""HTTP-API модуля web_search (/internal/web-search): просмотр + запуск (POST/engines)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.modules.web_search.api import router
from src.modules.web_search.constants import FETCH_STATUS_DONE
from src.modules.web_search.crud import page as page_crud
from src.modules.web_search.crud import query as query_crud
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.providers import registry
from src.modules.web_search.providers.base import FetchEngine, SearchEngine
from src.modules.web_search.providers.request import SearchRequest
from src.modules.web_search.services import searcher
from src.modules.web_search.services.searcher import Searcher


class _StubEngine(SearchEngine, FetchEngine):
    """Движок-заглушка (обе роли): без сети, пустая выдача → прогон завершается в ``done``."""

    code = "stub"
    enabled_field = "tavily_gateway_enabled"
    pages_per_request = 20

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        return []

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        return {url: None for url in urls}


@pytest.fixture
def use_stub(monkeypatch):
    """Зарегистрировать заглушку в обоих реестрах и сделать её дефолтным движком."""
    stub = _StubEngine()
    registry.search_engines.register(stub)
    registry.fetch_engines.register(stub)
    monkeypatch.setattr(Searcher, "_default_search_engine", lambda: "stub")
    monkeypatch.setattr(Searcher, "_default_fetch_engine", lambda: "stub")
    return stub


@pytest.fixture
async def app(config: Config):
    engine = await init_database(config)
    import src.modules.web_search.models  # noqa: F401 — register tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    fastapi_app = FastAPI()
    register_exception_handlers(fastapi_app)
    fastapi_app.include_router(router, prefix="/internal/web-search")
    try:
        yield fastapi_app
    finally:
        await close_database()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.db
async def test_list_queries_paginates_and_filters(client):
    await query_crud.query_create(
        search_engine="tavily", fetch_engine="tavily", query="vector db"
    )
    await query_crud.query_create(
        search_engine="firecrawl", fetch_engine="tavily", query="rust async"
    )

    r = await client.get("/internal/web-search/queries")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert len(body["items"]) == 2

    filtered = await client.get(
        "/internal/web-search/queries", params={"search_engine": "tavily"}
    )
    assert filtered.json()["total"] == 1


@pytest.mark.db
async def test_list_queries_sorts_by_whitelisted_column(client):
    await query_crud.query_create(
        search_engine="tavily", fetch_engine="tavily", query="q1"
    )
    await query_crud.query_create(
        search_engine="firecrawl", fetch_engine="tavily", query="q2"
    )
    await query_crud.query_create(
        search_engine="xai", fetch_engine="tavily", query="q3"
    )

    asc = await client.get(
        "/internal/web-search/queries",
        params={"sort_by": "search_engine", "sort_dir": "asc"},
    )
    engines = [i["search_engine"] for i in asc.json()["items"]]
    assert engines == ["firecrawl", "tavily", "xai"]

    desc = await client.get(
        "/internal/web-search/queries",
        params={"sort_by": "search_engine", "sort_dir": "desc"},
    )
    assert [i["search_engine"] for i in desc.json()["items"]] == ["xai", "tavily", "firecrawl"]


@pytest.mark.db
async def test_list_queries_unknown_sort_by_falls_back(client):
    await query_crud.query_create(
        search_engine="tavily", fetch_engine="tavily", query="q"
    )
    r = await client.get(
        "/internal/web-search/queries", params={"sort_by": "id; drop table"}
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.db
async def test_get_query_returns_results_with_page_fields(client):
    query = await query_crud.query_create(
        search_engine="tavily", fetch_engine="tavily", query="q"
    )
    page = await page_crud.page_upsert("https://example.com/p", title="Заголовок")
    await query_result_crud.result_add(
        query_code=query.code,
        page_code=page.code,
        rank=1,
        score=0.5,
        summary="Краткое содержание страницы",
        meta={"reason": "релевантно"},
    )

    r = await client.get(f"/internal/web-search/queries/{query.code}")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == query.code  # web_search коды голые (без префикса)
    assert body["query"] == "q"
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert result["page_url"] == "https://example.com/p"
    assert result["page_title"] == "Заголовок"
    assert result["page_status"] == "pending"
    assert result["summary"] == "Краткое содержание страницы"
    assert result["meta"] == {"reason": "релевантно"}


@pytest.mark.db
async def test_get_query_missing_returns_404(client):
    r = await client.get("/internal/web-search/queries/doesnotexist000000000000")
    assert r.status_code == 404
    assert r.json()["error"]


@pytest.mark.db
async def test_list_pages_filters_by_status(client):
    await page_crud.page_upsert("https://a.com")
    fetched = await page_crud.page_upsert("https://b.com")
    await page_crud.page_set_body(fetched.code, body="# body")

    r = await client.get(
        "/internal/web-search/pages", params={"status": FETCH_STATUS_DONE}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://b.com"
    assert "body" not in body["items"][0]  # список без тяжёлого контента


@pytest.mark.db
async def test_get_page_returns_content(client):
    page = await page_crud.page_upsert("https://example.com/c")
    await page_crud.page_set_body(page.code, body="# title\nbody")

    r = await client.get(f"/internal/web-search/pages/{page.code}")
    assert r.status_code == 200
    body = r.json()
    assert body["body"] == "# title\nbody"
    assert body["status"] == FETCH_STATUS_DONE


@pytest.mark.db
async def test_get_page_missing_returns_404(client):
    r = await client.get("/internal/web-search/pages/nonexistentcode000000")
    assert r.status_code == 404


@pytest.mark.db
async def test_list_engines_returns_available_and_defaults(client):
    r = await client.get("/internal/web-search/engines")
    assert r.status_code == 200
    body = r.json()
    assert "tavily" in body["search"] and "tavily" in body["fetch"]
    assert "xai" in body["search"] and "xai" not in body["fetch"]  # Grok контент не тянет
    assert body["search_default"] == "tavily"
    assert body["fetch_default"] == "tavily"


@pytest.mark.db
async def test_create_query_schedules_and_returns_pending(client, use_stub):
    r = await client.post("/internal/web-search/queries", json={"query": "hello"})
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "pending"  # fire-and-forget: сразу pending, клиент не ждёт
    assert body["query"] == "hello"
    assert len(body["code"]) == 22 and "@" not in body["code"]  # голый код без префикса

    await asyncio.gather(*list(searcher._BACKGROUND_TASKS))  # дождаться фонового прогона
    got = await query_crud.query_get(body["code"])
    assert got.status == "done"


@pytest.mark.db
async def test_create_query_rejects_invalid_body(client):
    empty = await client.post("/internal/web-search/queries", json={"query": ""})
    assert empty.status_code == 422  # query min_length=1
    too_many = await client.post(
        "/internal/web-search/queries", json={"query": "x", "max_results": 99}
    )
    assert too_many.status_code == 422  # max_results le=50


@pytest.mark.db
async def test_create_query_unknown_engine_returns_400(client):
    r = await client.post(
        "/internal/web-search/queries", json={"query": "x", "search_engine": "nope"}
    )
    assert r.status_code == 400  # неизвестный движок → bad_request (строка не создаётся)
