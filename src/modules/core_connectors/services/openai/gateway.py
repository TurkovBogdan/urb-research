"""Шлюз OpenAI — только расход (не инференс).

У OpenAI **нет** API остатка баланса (`credit_grants` — только браузерный session-токен,
протухает; см. ``AGENTS/research/openai/INDEX.md``). Программно доступен лишь **расход** через
Admin Costs API — нужен **Admin-ключ** ``sk-admin-…`` (обычный ``sk-…`` даёт 403/404).
Показываем метрику «Расход за N дней»: ``GET /organization/costs`` (bucket 1d) → сумма
``results[].amount.value`` (в долларах) по всем бакетам окна.
"""

from __future__ import annotations

import time
from typing import Any, ClassVar

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance

_SECONDS_PER_DAY = 86400


class OpenAIGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "openai"
    NAME: ClassVar[str] = "OpenAI"
    DESCRIPTION: ClassVar[str] = "LLM-провайдер OpenAI (GPT, o-серия, эмбеддинги)."
    BASE_URL: ClassVar[str] = "https://api.openai.com/v1"
    TIMEOUT: ClassVar[float] = 30.0
    API_KEY_FIELD: ClassVar[str] = "openai_admin_api_key"
    ENABLED_FIELD: ClassVar[str] = "openai_gateway_enabled"
    HAS_BALANCE: ClassVar[bool] = True
    SPEND_WINDOW_DAYS: ClassVar[int] = 30  # окно для метрики расхода

    async def costs(
        self, *, start_time: int, end_time: int | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        """``GET /organization/costs`` (Admin) — расход по дневным бакетам за окно."""
        params: dict[str, Any] = {"start_time": start_time, "bucket_width": "1d"}
        if end_time is not None:
            params["end_time"] = end_time
        if limit is not None:
            params["limit"] = limit
        return await self._request("GET", "/organization/costs", params=params)

    async def _fetch_balance(self) -> dict[str, Any]:
        start = int(time.time()) - self.SPEND_WINDOW_DAYS * _SECONDS_PER_DAY
        return await self.costs(start_time=start, limit=self.SPEND_WINDOW_DAYS + 1)

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Сумма расхода за окно: ``Σ data[].results[].amount.value`` (доллары). ⚠ `value` —
        строка высокой точности (напр. `"2.7141308…"`), не float → приводим `float(value)`."""
        total = 0.0
        for bucket in raw.get("data") or []:
            for result in bucket.get("results") or []:
                value = (result.get("amount") or {}).get("value")
                if value is not None:
                    total += float(value)
        metric = BalanceMetric.money(f"Расход {self.SPEND_WINDOW_DAYS}д", round(total, 2))
        return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=[metric])


__all__ = ["OpenAIGateway"]
