"""Шлюз Tavily: тонкий типизированный клиент к API, возвращает нативные ответы.

Метод принимает модель параметров, POST'ит её тело на эндпоинт и возвращает
НАТИВНЫЙ JSON-ответ Tavily без доменного маппинга — форму под конкретного
потребителя строит сам потребитель. HTTP-обвязка/ключ/тумблер — в ``ServiceGateway``.
Ключ берётся из настроек core_connectors. Аутентификация — ``Authorization: Bearer``.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.services.tavily.params import (
    TavilyCrawlParams,
    TavilyExtractParams,
    TavilyMapParams,
    TavilySearchParams,
)


class TavilyGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "tavily"
    NAME: ClassVar[str] = "Tavily"
    DESCRIPTION: ClassVar[str] = "Веб-поиск и извлечение контента страниц."
    BASE_URL: ClassVar[str] = "https://api.tavily.com"
    TIMEOUT: ClassVar[float] = 60.0
    API_KEY_FIELD: ClassVar[str] = "tavily_api_key"
    ENABLED_FIELD: ClassVar[str] = "tavily_gateway_enabled"
    HAS_BALANCE: ClassVar[bool] = True

    async def usage(self) -> dict[str, Any]:
        """Расход/лимит кредитов ключа и аккаунта (``GET /usage``): остаток =
        ``account.plan_limit - account.plan_usage``. Разбивка по методам внутри."""
        return await self._request("GET", "/usage")

    async def _fetch_balance(self) -> dict[str, Any]:
        return await self.usage()

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Кредитная метрика Tavily: использовано ``account.plan_usage`` из ``plan_limit``.
        Денежной суммы Tavily не отдаёт."""
        account = raw.get("account") or {}
        used = account.get("plan_usage")
        total = account.get("plan_limit")
        metrics = []
        if used is not None and total is not None:
            metrics.append(BalanceMetric.usage("Кредиты", used=used, total=total, unit="credits"))
        return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=metrics)

    async def search(self, params: TavilySearchParams) -> dict[str, Any]:
        return await self._post("/search", params.to_payload())

    async def extract(self, params: TavilyExtractParams) -> dict[str, Any]:
        return await self._post("/extract", params.to_payload())

    async def map(self, params: TavilyMapParams) -> dict[str, Any]:
        return await self._post("/map", params.to_payload())

    async def crawl(self, params: TavilyCrawlParams) -> dict[str, Any]:
        return await self._post("/crawl", params.to_payload())


__all__ = ["TavilyGateway"]
