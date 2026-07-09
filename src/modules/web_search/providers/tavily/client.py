"""Адаптер Tavily поверх коннектора ``core_connectors`` — умеет обе роли (поиск + контент).

HTTP/ключ/тумблер — на стороне коннектора (`core_connectors.services.tavily`); здесь только
доменный маппинг. Поиск (``/search``) → ссылки ``{url, rank, score, summary, title}``
(``summary`` = сниппет ``content``; ``title`` = заголовок документа; контент не тянем — это
отдельная роль). Контент (``/extract``, до ``pages_per_request`` url).
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.tavily import (
    TavilyExtractParams,
    TavilyGateway,
    TavilySearchParams,
)
from src.modules.web_search.providers.base import FetchEngine, SearchEngine
from src.modules.web_search.providers.request import SearchRequest


class TavilyEngine(SearchEngine, FetchEngine):
    code: ClassVar[str] = "tavily"
    enabled_field: ClassVar[str] = TavilyGateway.ENABLED_FIELD
    pages_per_request: ClassVar[int] = 20

    def __init__(self) -> None:
        self.gateway = TavilyGateway()

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        params = TavilySearchParams(
            query=request.query,
            max_results=request.max_results,
            include_domains=list(request.include_domains) or None,
            exclude_domains=list(request.exclude_domains) or None,
            time_range=request.time_range,
        )
        data = await self.gateway.search(params)
        return [
            {
                "url": item["url"],
                "rank": rank,
                "score": item.get("score"),
                "summary": item.get("content"),
                "title": item.get("title"),
            }
            for rank, item in enumerate(data.get("results", []), 1)
        ]

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        params = TavilyExtractParams(urls=urls, format="markdown", extract_depth="basic")
        data = await self.gateway.extract(params)
        by_url: dict[str, str | None] = {url: None for url in urls}
        for item in data.get("results") or []:
            by_url[item["url"]] = item.get("raw_content")
        return by_url


__all__ = ["TavilyEngine"]
