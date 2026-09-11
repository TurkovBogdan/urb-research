"""Адаптер daemon-web-scrapper поверх коннектора ``core_connectors`` — только контент.

HTTP/адрес/токен — на стороне модуля доступов; коннектор открывается на каждый вызов.
Демон умеет лишь скрейп страниц (не поиск), поэтому реализует одну роль — ``FetchEngine``.
Батч-эндпойнт демона берёт до ``pages_per_request`` url за запрос (параллелизм на его
стороне = ``SCRAPE_BATCH_CONCURRENCY``); ответ ``{results: [...]}`` мапим url → ``content``
(markdown главного контента страницы, ``None`` если извлечь нечего).
"""

from __future__ import annotations

from typing import ClassVar, cast

from src.modules.core_connectors.connectors.web_scrapper import (
    WebScrapperConnector,
    WebScrapperScrapBatchParams,
)
from src.modules.core_connectors.service import open_connector
from src.modules.web_search.providers.base import FetchEngine


class WebScrapperEngine(FetchEngine):
    code: ClassVar[str] = "web_scrapper"
    pages_per_request: ClassVar[int] = 10

    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        connector = cast(WebScrapperConnector, await open_connector(self.code))
        data = await connector.scrap_batch(WebScrapperScrapBatchParams(urls=urls))
        by_url: dict[str, str | None] = {url: None for url in urls}
        for item in data.get("results") or []:
            by_url[item["url"]] = item.get("content")
        return by_url


__all__ = ["WebScrapperEngine"]
