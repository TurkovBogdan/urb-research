"""Шлюз xAI Management — биллинг: баланс предоплаты и лимиты трат команды.

**Отдельная поверхность xAI** (не инференс): другая база ``management-api.x.ai`` и
**отдельный ключ** ``xai_management_api_key`` (Console → Settings → Management Keys;
право *Management Keys Read*/billing). Auth — та же схема ``Authorization: Bearer``, но
токен другой; inference-ключ здесь не работает. Все суммы — в **USD-центах**.

``team_id`` эндпойнты требуют в пути; он выводимый — ``XaiGateway.api_key_info().team_id``.
Низкоуровневые методы держим чистыми (``team_id`` параметром), а единый ``balance()``
резолвит ``team_id`` сам через инференс-гейтвей (для унифицированного вызова без аргументов).
Тумблера нет — гейтвей активен, если задан ключ.
"""

from __future__ import annotations

from typing import Any, ClassVar

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.services.xai.gateway import XaiGateway


class XaiManagementGateway(ServiceGateway):
    SERVICE: ClassVar[str] = "xai"
    NAME: ClassVar[str] = "xAI Management"
    DESCRIPTION: ClassVar[str] = "Биллинг xAI: баланс предоплаты и лимиты трат."
    BASE_URL: ClassVar[str] = "https://management-api.x.ai"
    TIMEOUT: ClassVar[float] = 60.0
    API_KEY_FIELD: ClassVar[str] = "xai_management_api_key"
    HAS_BALANCE: ClassVar[bool] = True

    async def _fetch_balance(self) -> dict[str, Any]:
        """team_id — из инференс-гейтвея (`api_key_info`), затем предоплатный баланс."""
        team_id = (await XaiGateway().api_key_info()).get("team_id")
        if not team_id:
            raise RuntimeError("xAI: team_id недоступен (нет доступа к inference api-key)")
        return await self.prepaid_balance(team_id)

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Предоплатный остаток xAI в USD. ⚠ Знак инвертирован: ``total.val`` отрицателен при
        наличии кредита (пополнения <0, списания >0) → **остаток = −total.val**, из центов в USD."""
        val = (raw.get("total") or {}).get("val")
        amount = -float(val) / 100 if val is not None else None
        metrics = [BalanceMetric.money("Баланс", amount)] if amount is not None else []
        return ConnectorBalance(service=self.SERVICE, name="xAI", metrics=metrics)

    async def prepaid_balance(self, team_id: str) -> dict[str, Any]:
        """Остаток предоплаты команды (``GET /v1/billing/teams/{team_id}/prepaid/balance``):
        ``total`` (баланс, USD-центы) + ``changes[]`` (история пополнений/списаний)."""
        return await self._request("GET", f"/v1/billing/teams/{team_id}/prepaid/balance")

    async def spending_limits(self, team_id: str) -> dict[str, Any]:
        """Лимиты постоплаты (``GET /v1/billing/teams/{team_id}/postpaid/spending-limits``):
        ``effectiveHardSl`` / ``softSl`` / ``effectiveSl`` (USD-центы)."""
        return await self._request(
            "GET", f"/v1/billing/teams/{team_id}/postpaid/spending-limits"
        )

    async def invoice_preview(self, team_id: str) -> dict[str, Any]:
        """Превью счёта за текущий период (``GET .../postpaid/invoice/preview``):
        ``coreInvoice`` + ``billingCycle`` + ``effectiveSpendingLimit`` (USD-центы)."""
        return await self._request(
            "GET", f"/v1/billing/teams/{team_id}/postpaid/invoice/preview"
        )


__all__ = ["XaiManagementGateway"]
