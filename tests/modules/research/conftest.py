"""Фикстуры research-тестов: in-memory БД + fastmcp-клиент MCP-сервера + stub веб-поиска.

``db`` строит схему (research + web_search-модели) на свежей ``:memory:``-базе. ``mcp`` поднимает
MCP-сервер research (auth=None, no-op audit) и отдаёт in-memory ``Client`` — тесты зовут тулы так
же, как их видит нейронка (с ``@``-префиксами, DTO, ошибками ``ToolError``). ``call`` — хелпер,
возвращающий ``structured_content``. ``use_search`` регистрирует stub-движок и монкипатчит дефолты
``Searcher`` — ``query_search_run`` наполняет источники детерминированно, без сети.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastmcp import Client
from fastmcp.server.middleware import Middleware

from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.mcp.context import McpServerContext
from src.modules.research.mcp import mcp_server
from src.modules.web_search.providers import registry
from src.modules.web_search.providers.base import FetchEngine, SearchEngine
from src.modules.web_search.providers.request import SearchRequest
from src.modules.web_search.services.searcher import Searcher


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    from src.core.database.runtime import Base
    import src.modules.research.models  # noqa: F401 — register research tables
    import src.modules.web_search.models  # noqa: F401 — register web_search tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.fixture
async def mcp(db):
    server = mcp_server(McpServerContext(auth=None, audit=Middleware(), allowed_hosts=[]))
    async with Client(server) as client:
        yield client


@pytest.fixture
def call(mcp):
    """Позвать тул и вернуть ``structured_content`` (dict). Ошибка тула → ``ToolError``."""

    async def _call(name: str, **args: Any):
        return (await mcp.call_tool(name, args)).structured_content

    return _call


class _StubSearch(SearchEngine, FetchEngine):
    """Движок-заглушка (обе роли): отдаёт заданные ссылки + контент, без сети.

    Url без записи в ``pages`` отдаёт пустой контент → страница ``error``/``empty``;
    ``fetch_raises`` роняет весь батч (эмуляция недоступного движка контента). ``results`` /
    ``pages`` / ``fetch_raises`` публичны: тест меняет их между прогонами, чтобы разыграть
    «сервис получения снова поднялся».
    """

    code = "stub"
    enabled_field = "tavily_gateway_enabled"  # доступность из core_connectors (дефолт True)

    def __init__(self, results=None, pages=None, fetch_raises=None) -> None:
        self.results = results or []
        self.pages = pages or {}
        self.fetch_raises = fetch_raises
        self.pages_per_request = 20

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        return self.results

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        if self.fetch_raises is not None:
            raise self.fetch_raises
        return {url: self.pages.get(url) for url in urls}


@pytest.fixture
def use_search(monkeypatch):
    """Установить stub веб-поиска: ``use_search(results=[...], pages={url: body}, fetch_raises=exc)``."""

    def _install(results=None, pages=None, fetch_raises=None) -> _StubSearch:
        stub = _StubSearch(results=results, pages=pages, fetch_raises=fetch_raises)
        registry.search_engines.register(stub)
        registry.fetch_engines.register(stub)
        monkeypatch.setattr(Searcher, "_default_search_engine", lambda: "stub")
        monkeypatch.setattr(Searcher, "_default_fetch_engine", lambda: "stub")
        return stub

    return _install
