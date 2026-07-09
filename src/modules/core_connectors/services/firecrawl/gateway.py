"""Шлюз Firecrawl: тонкий типизированный клиент к API, возвращает нативные ответы.

Метод принимает модель параметров, POST'ит её тело (camelCase) на эндпоинт ``/v2/*``
и возвращает НАТИВНЫЙ JSON-ответ Firecrawl без доменного маппинга. ``crawl`` —
асинхронный (отдаёт ``id``), статус тянет ``crawl_status(job_id)``. HTTP-обвязка/ключ/
тумблер — в ``ServiceGateway``. Ключ берётся из настроек core_connectors.
Аутентификация — ``Authorization: Bearer``.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.services.firecrawl.params import (
    FirecrawlCrawlParams,
    FirecrawlMapParams,
    FirecrawlScrapeParams,
    FirecrawlSearchParams,
)


class FirecrawlGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "firecrawl"
    NAME: ClassVar[str] = "Firecrawl"
    DESCRIPTION: ClassVar[str] = "Скрапинг, поиск и обход сайтов."
    BASE_URL: ClassVar[str] = "https://api.firecrawl.dev"
    TIMEOUT: ClassVar[float] = 120.0
    API_KEY_FIELD: ClassVar[str] = "firecrawl_api_key"
    ENABLED_FIELD: ClassVar[str] = "firecrawl_gateway_enabled"
    HAS_BALANCE: ClassVar[bool] = True

    async def usage(self) -> dict[str, Any]:
        """Остаток кредитов команды (``GET /v2/team/credit-usage``):
        ``data.remainingCredits`` / ``data.planCredits`` + границы биллинг-периода."""
        return await self._request("GET", "/v2/team/credit-usage")

    async def _fetch_balance(self) -> dict[str, Any]:
        return await self.usage()

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Кредитная метрика Firecrawl: использовано = ``planCredits - remainingCredits`` из
        ``planCredits``. Отдельная ось токенов (``token_usage``) сюда пока не входит."""
        data = raw.get("data") or {}
        available = data.get("remainingCredits")
        total = data.get("planCredits")
        used = total - available if total is not None and available is not None else None
        metrics = []
        if used is not None and total is not None:
            metrics.append(BalanceMetric.usage("Кредиты", used=used, total=total, unit="credits"))
        return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=metrics)

    async def scrape(self, params: FirecrawlScrapeParams) -> dict[str, Any]:
        return await self._post("/v2/scrape", params.to_payload())

    async def search(self, params: FirecrawlSearchParams) -> dict[str, Any]:
        return await self._post("/v2/search", params.to_payload())

    async def map(self, params: FirecrawlMapParams) -> dict[str, Any]:
        return await self._post("/v2/map", params.to_payload())

    async def crawl(self, params: FirecrawlCrawlParams) -> dict[str, Any]:
        """Стартует обход (async): ответ ``{id, url}``; статус — ``crawl_status(id)``."""
        return await self._post("/v2/crawl", params.to_payload())

    async def crawl_status(self, job_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v2/crawl/{job_id}")


__all__ = ["FirecrawlGateway"]
