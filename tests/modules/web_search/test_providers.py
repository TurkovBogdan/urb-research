"""web_search: реестры движков поиска / контента (+ учёт доступности) и норм. выдача."""

from __future__ import annotations

from typing import Any

import pytest

from src.modules.web_search.providers import (
    SearchRequest,
    fetch_engines,
    search_engines,
)
from src.modules.web_search.providers import base
from src.modules.web_search.providers.base import FetchedPage, SearchEngine


def _connector_with(**methods: Any):
    """Подмена ``open_connector``: коннектор-заглушка с заданными методами.

    Адаптер берёт коннектор на каждый вызов через модуль доступов, поэтому шов теста
    проходит именно здесь — ни ключа, ни записи доступа для маппинга не нужно.
    """
    connector = type(
        "_StubConnector", (), {name: staticmethod(fn) for name, fn in methods.items()}
    )()

    async def _open(_service: str, **_kwargs: Any):
        return connector

    return _open


@pytest.mark.pure
def test_search_registry_has_all_engines():
    assert set(search_engines.codes()) >= {"tavily", "firecrawl", "xai"}  # Grok — движок поиска
    assert search_engines.get("tavily").code == "tavily"
    assert search_engines.get("xai").code == "xai"


@pytest.mark.pure
def test_fetch_registry_excludes_search_only_engines():
    assert set(fetch_engines.codes()) >= {"tavily", "firecrawl", "simple_web_scraper"}
    assert "xai" not in fetch_engines.codes()  # Grok контент не тянет
    assert fetch_engines.get("firecrawl").code == "firecrawl"


@pytest.mark.pure
def test_simple_web_scraper_is_fetch_only():
    assert fetch_engines.get("simple_web_scraper").code == "simple_web_scraper"
    assert "simple_web_scraper" not in search_engines.codes()  # скрейпер не ищет, только фетч


@pytest.mark.pure
async def test_simple_web_scraper_takes_the_outcome_not_the_content(monkeypatch):
    from src.modules.web_search.providers.simple_web_scraper import client as scraper_client
    from src.modules.web_search.providers.simple_web_scraper.client import SimpleWebScraperEngine

    async def _fake_scrap_batch(_params: Any) -> dict[str, Any]:
        return {
            "results": [
                {"url": "https://a.com", "outcome": "ok", "content": "# A"},
                {"url": "https://moved.com", "outcome": "redirected", "content": "# Moved"},
                # Стена ботозащиты приходит с текстом — это не материал страницы
                {"url": "https://wall.ru", "outcome": "access_denied", "content": "Подтвердите…"},
                {"url": "https://gone.com", "outcome": "not_found", "content": None},
                {"url": "https://blank.com", "outcome": "ok", "content": ""},
                # Ответ без вердикта — не повод верить тексту
                {"url": "https://odd.com", "content": "# Без outcome"},
            ],
            "elapsed_ms": 12,
        }

    monkeypatch.setattr(
        scraper_client,
        "open_connector",
        _connector_with(scrap_batch=_fake_scrap_batch),
    )

    pages = await SimpleWebScraperEngine().fetch_pages(
        [
            "https://a.com",
            "https://moved.com",
            "https://wall.ru",
            "https://gone.com",
            "https://blank.com",
            "https://odd.com",
            "https://missing.com",
        ]
    )

    assert pages == {
        "https://a.com": FetchedPage(content="# A"),
        "https://moved.com": FetchedPage(content="# Moved"),
        "https://wall.ru": FetchedPage(error="access_denied"),
        "https://gone.com": FetchedPage(error="not_found"),
        "https://blank.com": FetchedPage(error="empty"),
        "https://odd.com": FetchedPage(error="empty"),
        "https://missing.com": FetchedPage(error="empty"),  # url нет в ответе демона
    }


def _record_opening(monkeypatch, client_module: Any, **methods: Any) -> list[Any]:
    """Подменить ``open_connector`` адаптера коннектором с ``methods``; вернуть список
    подключений, через которые адаптер его открывал."""
    opened: list[Any] = []

    async def _open(_service: str, **kwargs: Any):
        opened.append(kwargs.get("access"))
        return type("_Stub", (), {name: staticmethod(fn) for name, fn in methods.items()})()

    monkeypatch.setattr(client_module, "open_connector", _open)
    return opened


@pytest.mark.pure
async def test_simple_web_scraper_goes_through_the_connection_of_its_route(monkeypatch):
    from src.modules.web_search.providers.simple_web_scraper import client as scraper_client
    from src.modules.web_search.providers.simple_web_scraper.client import SimpleWebScraperEngine

    async def _scrap_batch(_params: Any) -> dict[str, Any]:
        return {"results": []}

    opened = _record_opening(monkeypatch, scraper_client, scrap_batch=_scrap_batch)

    await SimpleWebScraperEngine().fetch_pages(["https://a.ru"], access=6)

    assert opened == [6]


@pytest.mark.pure
async def test_tavily_gives_each_url_its_material_or_a_reason(monkeypatch):
    from src.modules.web_search.providers.tavily import client as tavily_client
    from src.modules.web_search.providers.tavily.client import TavilyEngine

    async def _extract(_params: Any) -> dict[str, Any]:
        return {
            "results": [
                {"url": "https://a.com", "raw_content": "# A"},
                {"url": "https://blank.com", "raw_content": ""},
            ]
        }

    opened = _record_opening(monkeypatch, tavily_client, extract=_extract)

    pages = await TavilyEngine().fetch_pages(
        ["https://a.com", "https://blank.com", "https://lost.com"], access=3
    )

    assert pages == {
        "https://a.com": FetchedPage(content="# A"),
        "https://blank.com": FetchedPage(error="empty"),
        "https://lost.com": FetchedPage(error="empty"),  # Tavily не вернул url вовсе
    }
    assert opened == [3]


@pytest.mark.pure
async def test_firecrawl_scrapes_each_url_through_the_connection_of_its_route(monkeypatch):
    from src.modules.web_search.providers.firecrawl import client as firecrawl_client
    from src.modules.web_search.providers.firecrawl.client import FirecrawlEngine

    async def _scrape(params: Any) -> dict[str, Any]:
        return {"data": {"markdown": f"# {params.url}"}} if "ok" in params.url else {"data": {}}

    opened = _record_opening(monkeypatch, firecrawl_client, scrape=_scrape)

    pages = await FirecrawlEngine().fetch_pages(["https://ok.com", "https://no.com"], access=4)

    assert pages == {
        "https://ok.com": FetchedPage(content="# https://ok.com"),
        "https://no.com": FetchedPage(error="empty"),
    }
    assert opened == [4]


@pytest.mark.pure
def test_registry_unknown_raises():
    with pytest.raises(KeyError):
        search_engines.get("nope")
    with pytest.raises(KeyError):
        fetch_engines.get("nope")


@pytest.mark.pure
async def test_registry_reflects_access_readiness(monkeypatch):
    async def _ready(service: str, *, access: int | None = None) -> bool:
        return service != "xai"

    monkeypatch.setattr(base, "access_available", _ready)

    available = await search_engines.available_codes()
    assert "xai" not in available  # доступа к xAI нет → движок недоступен
    assert "tavily" in available
    assert await search_engines.is_available("tavily") is True
    assert await search_engines.is_available("xai") is False


class _FakeEngine(SearchEngine):
    code = "fake"

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        return [
            {"url": "https://a.com/x", "rank": 1, "score": 0.7, "meta": {"title": "A"}},
            {"url": "http://b.com/y", "rank": 2},
        ]


@pytest.mark.pure
async def test_engine_search_returns_normalized_links():
    results = await _FakeEngine().search(SearchRequest(query="q", max_results=2))

    assert [r["url"] for r in results] == ["https://a.com/x", "http://b.com/y"]
    assert results[0]["meta"] == {"title": "A"}


def _xai_response(links: list[dict[str, Any]], sources: list[str]) -> dict[str, Any]:
    import json

    return {
        "output": [
            {
                "type": "web_search_call",
                "action": {"sources": [{"url": u} for u in sources]},
            },
            {
                "type": "message",
                "content": [{"text": json.dumps({"links": links})}],
            },
        ]
    }


@pytest.mark.pure
async def test_xai_search_drops_ungrounded_links(monkeypatch):
    from src.modules.web_search.providers.xai import client as xai_client
    from src.modules.web_search.providers.xai.client import XaiSearchEngine

    links = [
        {"url": "https://real.com/a", "title": "A", "reason": "r1", "relevance": 0.9},
        {"url": "https://made-up.com/x", "title": "X", "reason": "r2", "relevance": 0.8},
        {"url": "https://real.com/b/", "title": "B", "reason": "r3", "relevance": 0.7},
    ]
    payload = _xai_response(links, sources=["https://real.com/a", "https://real.com/b"])

    async def _fake_responses(_params: Any) -> dict[str, Any]:
        return payload

    monkeypatch.setattr(xai_client, "open_connector", _connector_with(responses=_fake_responses))

    results = await XaiSearchEngine().search(SearchRequest(query="q", max_results=5))

    assert [r["url"] for r in results] == ["https://real.com/a", "https://real.com/b/"]
    assert [r["rank"] for r in results] == [1, 2]
    assert results[0]["score"] == 0.9
    assert results[0]["title"] == "A"  # заголовок — верхний ключ (→ web_search_page.title)
    assert results[0]["meta"] == {"reason": "r1"}  # meta — только контекстное


@pytest.mark.pure
async def test_xai_search_survives_unparseable_output(monkeypatch):
    from src.modules.web_search.providers.xai import client as xai_client
    from src.modules.web_search.providers.xai.client import XaiSearchEngine

    async def _fake_responses(_params: Any) -> dict[str, Any]:
        return {"output": [{"type": "message", "content": [{"text": "not json"}]}]}

    monkeypatch.setattr(xai_client, "open_connector", _connector_with(responses=_fake_responses))

    assert await XaiSearchEngine().search(SearchRequest(query="q")) == []
