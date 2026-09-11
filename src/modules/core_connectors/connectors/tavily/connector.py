"""Коннектор Tavily: тонкий типизированный клиент к API, возвращает нативные ответы.

Метод принимает модель параметров, POST'ит её тело на эндпоинт и возвращает НАТИВНЫЙ
JSON-ответ Tavily без доменного маппинга — форму под конкретного потребителя строит сам
потребитель. HTTP/адрес/авторизация — в ``HttpConnector``; ключ приходит записью доступа.
Аутентификация — ``Authorization: Bearer``.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.core.settings import Field, StrField
from src.modules.core_connectors.connectors.base import HttpConnector
from src.modules.core_connectors.connectors.groups import GROUP_SEARCH
from src.modules.core_connectors.connectors.passport import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.connectors.tavily.params import (
    TavilyCrawlParams,
    TavilyExtractParams,
    TavilyMapParams,
    TavilySearchParams,
)


class TavilyConnector(HttpConnector):
    SERVICE: ClassVar[str] = "tavily"
    NAME: ClassVar[str] = "Tavily"
    DESCRIPTION: ClassVar[str] = "Веб-поиск и извлечение контента страниц."
    GROUP: ClassVar[str] = GROUP_SEARCH
    BASE_URL: ClassVar[str] = "https://api.tavily.com"
    TIMEOUT: ClassVar[float] = 60.0
    FIELDS: ClassVar[tuple[Field, ...]] = (
        StrField(
            key="api_key",
            label="API-ключ",
            description="Секретный ключ доступа к API Tavily. Получить: [app.tavily.com](https://app.tavily.com/home).",
            secret=True,
        ),
    )
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)

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


__all__ = ["TavilyConnector"]
