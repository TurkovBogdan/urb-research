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
from src.modules.web_search.providers.base import SearchEngine


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
    assert set(fetch_engines.codes()) >= {"tavily", "firecrawl", "web_scrapper"}
    assert "xai" not in fetch_engines.codes()  # Grok контент не тянет
    assert fetch_engines.get("firecrawl").code == "firecrawl"


@pytest.mark.pure
def test_web_scrapper_is_fetch_only():
    assert fetch_engines.get("web_scrapper").code == "web_scrapper"
    assert "web_scrapper" not in search_engines.codes()  # daemon-web-scrapper не ищет, только фетч


@pytest.mark.pure
async def test_web_scrapper_maps_batch_content_by_url(monkeypatch):
    from src.modules.web_search.providers.web_scrapper import client as web_scrapper_client
    from src.modules.web_search.providers.web_scrapper.client import WebScrapperEngine

    async def _fake_scrap_batch(_params: Any) -> dict[str, Any]:
        return {
            "results": [
                {"url": "https://a.com", "outcome": "ok", "content": "# A"},
                {"url": "https://b.com", "outcome": "timeout", "content": None},
            ],
            "elapsed_ms": 12,
        }

    monkeypatch.setattr(
        web_scrapper_client,
        "open_connector",
        _connector_with(scrap_batch=_fake_scrap_batch),
    )

    pages = await WebScrapperEngine().fetch_pages(
        ["https://a.com", "https://b.com", "https://c.com"]
    )

    assert pages == {
        "https://a.com": "# A",
        "https://b.com": None,  # неуспешный outcome — контента нет
        "https://c.com": None,  # url отсутствует в ответе — остаётся None
    }


@pytest.mark.pure
def test_registry_unknown_raises():
    with pytest.raises(KeyError):
        search_engines.get("nope")
    with pytest.raises(KeyError):
        fetch_engines.get("nope")


@pytest.mark.pure
async def test_registry_reflects_access_readiness(monkeypatch):
    async def _ready(service: str) -> bool:
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
