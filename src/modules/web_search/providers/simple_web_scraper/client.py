"""Адаптер simple-web-scraper поверх коннектора ``core_connectors`` — только контент.

HTTP/адрес/токен — на стороне модуля доступов; коннектор открывается на каждый вызов, через
подключение, которое выбрал маршрут (у скрейпера их бывает несколько: напрямую, через VPN).
Демон умеет лишь скрейп страниц (не поиск), поэтому реализует одну роль — ``FetchEngine``.
Батч-эндпойнт демона берёт до ``pages_per_request`` url за запрос (параллелизм на его
стороне = ``SCRAPE_BATCH_CONCURRENCY``).

Итог страницы решает ``outcome`` демона, а не наличие ``content``: заблокированная страница
приходит с текстом стены ботозащиты, и без этой проверки она сохранялась как успешная.
Неуспешный ``outcome`` уходит в причину как есть (``access_denied``, ``not_found``, …) —
по ней поиск решает, отдавать ли страницу запасному движку.
"""

from __future__ import annotations

from typing import Any, ClassVar, cast

from src.modules.core_connectors.connectors.simple_web_scraper import (
    SimpleWebScraperConnector,
    SimpleWebScraperScrapBatchParams,
)
from src.modules.core_connectors.service import open_connector
from src.modules.web_search.providers.base import FetchedPage, FetchEngine, fetched

# Исходы, при которых в ``content`` лежит сама страница; при прочих — то, что показал сайт.
_SUCCESS_OUTCOMES = frozenset({"ok", "redirected"})


class SimpleWebScraperEngine(FetchEngine):
    code: ClassVar[str] = "simple_web_scraper"
    pages_per_request: ClassVar[int] = 10

    async def fetch_pages(
        self, urls: list[str], *, access: int | None = None
    ) -> dict[str, FetchedPage]:
        connector = cast(
            SimpleWebScraperConnector, await open_connector(self.code, access=access)
        )
        data = await connector.scrap_batch(SimpleWebScraperScrapBatchParams(urls=urls))
        pages = {url: FetchedPage(error="empty") for url in urls}
        for item in data.get("results") or []:
            pages[item["url"]] = _page_of(item)
        return pages


def _page_of(item: dict[str, Any]) -> FetchedPage:
    outcome = item.get("outcome")
    if outcome not in _SUCCESS_OUTCOMES:
        return FetchedPage(error=outcome or "empty")
    return fetched(item.get("content"))


__all__ = ["SimpleWebScraperEngine"]
