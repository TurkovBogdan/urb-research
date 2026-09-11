"""Коннектор OpenRouter — только баланс/лимиты ключа (не инференс).

Полный провайдер OpenRouter (chat completions, provider-routing, structured output, каталог
моделей) сюда НЕ тянем — для наблюдаемости нужен лишь остаток. HTTP/адрес/авторизация — в
``HttpConnector``, база ``openrouter.ai/api/v1``, auth ``Bearer``. Все суммы — USD (float).

Баланс = **две независимые метрики** (сверено живьём, см. ``AGENTS/research/openrouter/INDEX.md``):
- «Лимит ключа» — ``GET /api/v1/key``: ``usage`` из ``limit`` (потолок трат ключа);
- «Баланс» — ``GET /api/v1/credits``: ``total_credits − total_usage`` (может быть отрицательным).
``/credits`` — best-effort: если недоступен, остаётся метрика лимита.
"""

from __future__ import annotations

from typing import Any, ClassVar

import httpx

from src.core.settings import Field, StrField
from src.modules.core_connectors.connectors.base import HttpConnector
from src.modules.core_connectors.connectors.groups import GROUP_MODELS
from src.modules.core_connectors.connectors.passport import BalanceMetric, ConnectorBalance


class OpenRouterConnector(HttpConnector):
    SERVICE: ClassVar[str] = "openrouter"
    NAME: ClassVar[str] = "OpenRouter"
    DESCRIPTION: ClassVar[str] = "Единый API-шлюз к LLM разных провайдеров."
    GROUP: ClassVar[str] = GROUP_MODELS
    BASE_URL: ClassVar[str] = "https://openrouter.ai/api/v1"
    TIMEOUT: ClassVar[float] = 30.0
    FIELDS: ClassVar[tuple[Field, ...]] = (
        StrField(
            key="api_key",
            label="API-ключ",
            description="Секретный ключ доступа к API OpenRouter. Получить: [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys).",
            secret=True,
        ),
    )
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)

    async def key_info(self) -> dict[str, Any]:
        """``GET /api/v1/key`` — лимит/остаток/расход ключа (``data.usage``/``limit``/…)."""
        return await self._request("GET", "/key")

    async def credits(self) -> dict[str, Any]:
        """``GET /api/v1/credits`` — ``data.total_credits``/``total_usage`` (кредиты аккаунта)."""
        return await self._request("GET", "/credits")

    async def _fetch_balance(self) -> dict[str, Any]:
        """Лимит ключа — обязателен; кредиты аккаунта — best-effort (могут быть недоступны)."""
        key = await self.key_info()
        try:
            account_credits = await self.credits()
        except httpx.HTTPError:
            account_credits = None
        return {"key": key, "credits": account_credits}

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        metrics: list[BalanceMetric] = []

        key_data = (raw.get("key") or {}).get("data") or {}
        usage, limit = key_data.get("usage"), key_data.get("limit")
        if usage is not None and limit is not None:
            metrics.append(BalanceMetric.usage("Лимит ключа", used=usage, total=limit, unit="USD"))

        credits_data = (raw.get("credits") or {}).get("data") or {}
        total, used = credits_data.get("total_credits"), credits_data.get("total_usage")
        if total is not None and used is not None:
            metrics.append(BalanceMetric.money("Баланс", round(total - used, 4)))

        return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=metrics)


__all__ = ["OpenRouterConnector"]
