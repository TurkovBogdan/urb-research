"""Адаптер Firecrawl поверх коннектора ``core_connectors`` — умеет обе роли (поиск + контент).

HTTP/ключ/тумблер — на стороне коннектора (`core_connectors.services.firecrawl`); здесь только
доменный маппинг. Поиск (``/v2/search`` → ``data.web[]``) → ссылки
``{url, rank, score:None, summary, title}`` (``summary`` = ``description``, ``title`` =
заголовок; score не отдаёт). Контент — ``/v2/scrape`` берёт один url за запрос → ``pages_per_request = 1``.
Домены Firecrawl-поиск не фильтрует.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.firecrawl import (
    FirecrawlGateway,
    FirecrawlScrapeParams,
    FirecrawlSearchParams,
)
from src.modules.web_search.providers.base import FetchEngine, SearchEngine
from src.modules.web_search.providers.request import SearchRequest

_TBS = {"day": "qdr:d", "week": "qdr:w", "month": "qdr:m", "year": "qdr:y"}


class FirecrawlEngine(SearchEngine, FetchEngine):
    code: ClassVar[str] = "firecrawl"
    enabled_field: ClassVar[str] = FirecrawlGateway.ENABLED_FIELD
    pages_per_request: ClassVar[int] = 1

    def __init__(self) -> None:
        self.gateway = FirecrawlGateway()

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        params = FirecrawlSearchParams(
            query=request.query,
            limit=request.max_results,
            tbs=_TBS.get(request.time_range) if request.time_range else None,
        )
        data = await self.gateway.search(params)
        web = (data.get("data") or {}).get("web") or []
        return [
            {
                "url": item["url"],
                "rank": rank,
                "score": None,
                "summary": item.get("description"),
                "title": item.get("title"),
            }
            for rank, item in enumerate(web, 1)
        ]

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        by_url: dict[str, str | None] = {}
        for url in urls:
            data = await self.gateway.scrape(FirecrawlScrapeParams(url=url, formats=["markdown"]))
            by_url[url] = (data.get("data") or {}).get("markdown")
        return by_url


__all__ = ["FirecrawlEngine"]
