"""Адаптер daemon-web-scrapper поверх коннектора ``core_connectors`` — только контент.

HTTP/тумблер — на стороне коннектора (`core_connectors.services.web_scrapper`); здесь только
доменный маппинг. Демон умеет лишь скрейп страниц (не поиск), поэтому реализует одну роль —
``FetchEngine``. Батч-эндпойнт демона берёт до ``pages_per_request`` url за запрос (параллелизм
на его стороне = ``SCRAPE_BATCH_CONCURRENCY``); ответ ``{results: [...]}`` мапим url →
``content`` (markdown главного контента страницы, ``None`` если извлечь нечего).
"""

from __future__ import annotations

from typing import ClassVar

from src.modules.core_connectors.services.web_scrapper import (
    WebScrapperGateway,
    WebScrapperScrapBatchParams,
)
from src.modules.web_search.providers.base import FetchEngine


class WebScrapperEngine(FetchEngine):
    code: ClassVar[str] = "web_scrapper"
    enabled_field: ClassVar[str] = WebScrapperGateway.ENABLED_FIELD
    pages_per_request: ClassVar[int] = 10

    def __init__(self) -> None:
        self.gateway = WebScrapperGateway()

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        data = await self.gateway.scrap_batch(WebScrapperScrapBatchParams(urls=urls))
        by_url: dict[str, str | None] = {url: None for url in urls}
        for item in data.get("results") or []:
            by_url[item["url"]] = item.get("content")
        return by_url


__all__ = ["WebScrapperEngine"]
