"""Шлюз Anthropic (Claude) — только расход (не инференс).

У Anthropic **нет** API остатка баланса (только console; см. ``AGENTS/research/anthropic/INDEX.md``).
Программно доступен лишь **расход** через Admin API Cost Report — нужен **Admin-ключ**
``sk-ant-admin…`` (обычный ``sk-ant-api…`` доступа не даёт). Auth у Anthropic — заголовок
``x-api-key`` + ``anthropic-version`` (не ``Bearer``; см. ``_auth_headers``).

Показываем метрику «Расход за N дней»: ``GET /organizations/cost_report`` (bucket 1d) → сумма
``results[].amount`` (⚠ **строка в ЦЕНТАХ** → ``Σ float(amount) / 100`` = доллары).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, ClassVar

from src.core.utils.date import utc_now
from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance


class AnthropicGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "anthropic"
    NAME: ClassVar[str] = "Anthropic (Claude)"
    DESCRIPTION: ClassVar[str] = "LLM-провайдер Anthropic (Claude)."
    BASE_URL: ClassVar[str] = "https://api.anthropic.com/v1"
    TIMEOUT: ClassVar[float] = 30.0
    API_KEY_FIELD: ClassVar[str] = "anthropic_admin_api_key"
    ENABLED_FIELD: ClassVar[str] = "anthropic_gateway_enabled"
    HAS_BALANCE: ClassVar[bool] = True
    SPEND_WINDOW_DAYS: ClassVar[int] = 30
    ANTHROPIC_VERSION: ClassVar[str] = "2023-06-01"

    def _auth_headers(self) -> dict[str, str]:
        return {"x-api-key": self._key(), "anthropic-version": self.ANTHROPIC_VERSION}

    async def cost_report(
        self, *, starting_at: str, ending_at: str | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        """``GET /organizations/cost_report`` (Admin) — расход по дневным бакетам за окно."""
        params: dict[str, Any] = {"starting_at": starting_at, "bucket_width": "1d"}
        if ending_at is not None:
            params["ending_at"] = ending_at
        if limit is not None:
            params["limit"] = limit
        return await self._request("GET", "/organizations/cost_report", params=params)

    async def _fetch_balance(self) -> dict[str, Any]:
        starting_at = (utc_now() - timedelta(days=self.SPEND_WINDOW_DAYS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return await self.cost_report(starting_at=starting_at, limit=self.SPEND_WINDOW_DAYS + 1)

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Сумма расхода за окно. ⚠ `amount` — строка в ЦЕНТАХ → ``Σ float(amount) / 100`` = доллары."""
        total_cents = 0.0
        for bucket in raw.get("data") or []:
            for result in bucket.get("results") or []:
                amount = result.get("amount")
                if amount is not None:
                    total_cents += float(amount)
        metric = BalanceMetric.money(f"Расход {self.SPEND_WINDOW_DAYS}д", round(total_cents / 100, 2))
        return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=[metric])


__all__ = ["AnthropicGateway"]
