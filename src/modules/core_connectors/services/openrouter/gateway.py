"""Шлюз OpenRouter — только баланс/лимиты ключа (не инференс).

Полный провайдер OpenRouter (chat completions, provider-routing, structured output, каталог
моделей) в коннекторы НЕ тянем — для мониторинга нужен лишь остаток. HTTP-обвязка/ключ/тумблер
— в ``ServiceGateway``, база ``openrouter.ai/api/v1``, auth ``Bearer``. Все суммы — USD (float).

Баланс = **две независимые метрики** (сверено живьём, см. ``AGENTS/research/openrouter/INDEX.md``):
- «Лимит ключа» — ``GET /api/v1/key``: ``usage`` из ``limit`` (потолок трат ключа);
- «Баланс» — ``GET /api/v1/credits``: ``total_credits − total_usage`` (может быть отрицательным).
``/credits`` — best-effort: если недоступен, остаётся метрика лимита.
"""

from __future__ import annotations

from typing import Any, ClassVar

import httpx

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance


class OpenRouterGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "openrouter"
    NAME: ClassVar[str] = "OpenRouter"
    DESCRIPTION: ClassVar[str] = "Единый API-шлюз к LLM разных провайдеров."
    BASE_URL: ClassVar[str] = "https://openrouter.ai/api/v1"
    TIMEOUT: ClassVar[float] = 30.0
    API_KEY_FIELD: ClassVar[str] = "openrouter_api_key"
    ENABLED_FIELD: ClassVar[str] = "openrouter_gateway_enabled"
    HAS_BALANCE: ClassVar[bool] = True

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


__all__ = ["OpenRouterGateway"]
