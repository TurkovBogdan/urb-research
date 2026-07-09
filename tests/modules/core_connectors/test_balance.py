"""core_connectors: паспорт коннекторов + нормализация баланса (маппинг → DTO) + реестр.

Маппинг — чистые функции над реальными формами ответов (сверены живьём, см.
`AGENTS/research/xai/INDEX.md` и docstrings гейтвеев). Сеть не трогаем: тестируем
``_parse_balance`` напрямую и ``ConnectorsRegistry`` — на стаб-коннекторах.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

import pytest

from src.modules.core_connectors.services.base import ServiceGateway
from src.modules.core_connectors.services.dto import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.services.firecrawl import FirecrawlGateway
from src.modules.core_connectors.registry import ConnectorsRegistry
from src.modules.core_connectors.services.anthropic import AnthropicGateway
from src.modules.core_connectors.services.openai import OpenAIGateway
from src.modules.core_connectors.services.openrouter import OpenRouterGateway
from src.modules.core_connectors.services.tavily import TavilyGateway
from src.modules.core_connectors.services.xai import XaiManagementGateway


@pytest.mark.pure
def test_tavily_balance_maps_credits_metric():
    bal = TavilyGateway()._parse_balance({"account": {"plan_usage": 17, "plan_limit": 1000}})
    assert (bal.service, bal.name) == ("tavily", "Tavily")
    assert len(bal.metrics) == 1
    m = bal.metrics[0]
    assert (m.label, m.unit) == ("Кредиты", "credits")
    assert (m.used, m.total, m.used_percent) == (17, 1000, 1.7)  # 17 / 1000
    assert m.amount is None  # Tavily не в деньгах


@pytest.mark.pure
def test_firecrawl_balance_maps_credits_metric():
    bal = FirecrawlGateway()._parse_balance({"data": {"remainingCredits": 898, "planCredits": 1000}})
    m = bal.metrics[0]
    assert (m.used, m.total, m.used_percent) == (102, 1000, 10.2)  # planCredits - remaining
    assert m.amount is None


@pytest.mark.pure
def test_xai_balance_negates_total_to_usd_metric():
    # total.val отрицателен при наличии кредита → остаток = -total.val (из центов)
    bal = XaiManagementGateway()._parse_balance({"total": {"val": "-602"}})
    assert (bal.service, bal.name) == ("xai", "xAI")
    m = bal.metrics[0]
    assert (m.label, m.currency) == ("Баланс", "USD")
    assert m.amount == pytest.approx(6.02)
    assert m.used is None and m.total is None


@pytest.mark.pure
def test_openrouter_balance_two_metrics():
    raw = {
        "key": {"data": {"usage": 5.16, "limit": 10}},
        "credits": {"data": {"total_credits": 5, "total_usage": 5.16}},
    }
    bal = OpenRouterGateway()._parse_balance(raw)
    assert bal.service == "openrouter"
    assert [m.label for m in bal.metrics] == ["Лимит ключа", "Баланс"]
    limit, balance = bal.metrics
    assert (limit.used, limit.total, limit.unit, limit.used_percent) == (5.16, 10, "USD", 51.6)
    assert balance.amount == pytest.approx(-0.16)  # total_credits - total_usage, может быть минус


@pytest.mark.pure
def test_openrouter_balance_limit_only_when_no_credits():
    # /credits недоступен (best-effort) → остаётся только метрика лимита ключа
    bal = OpenRouterGateway()._parse_balance({"key": {"data": {"usage": 1, "limit": 10}}, "credits": None})
    assert [m.label for m in bal.metrics] == ["Лимит ключа"]


@pytest.mark.pure
def test_openai_spend_sums_buckets():
    # ⚠ реальный API отдаёт amount.value СТРОКОЙ высокой точности, не float
    raw = {
        "data": [
            {"results": [{"amount": {"value": "0.06", "currency": "usd"}}]},
            {"results": [{"amount": {"value": "0.13"}}, {"amount": {"value": "0.01"}}]},
        ]
    }
    bal = OpenAIGateway()._parse_balance(raw)
    assert bal.service == "openai"
    m = bal.metrics[0]
    assert m.label == "Расход 30д"
    assert m.amount == 0.2  # 0.06 + 0.13 + 0.01, округлено


@pytest.mark.pure
def test_openai_spend_empty_is_zero():
    bal = OpenAIGateway()._parse_balance({"data": []})
    assert bal.metrics[0].amount == 0.0  # нет трат → $0, а не отсутствие метрики


@pytest.mark.pure
def test_anthropic_spend_cents_string_to_dollars():
    # ⚠ Anthropic: amount — строка в ЦЕНТАХ → Σ/100 = доллары
    raw = {
        "data": [
            {"results": [{"amount": "123.45", "currency": "USD"}]},
            {"results": [{"amount": "76.55"}]},
        ]
    }
    bal = AnthropicGateway()._parse_balance(raw)
    assert bal.service == "anthropic"
    m = bal.metrics[0]
    assert m.label == "Расход 30д"
    assert m.amount == 2.0  # (123.45 + 76.55) центов / 100 = $2.00


@pytest.mark.pure
def test_anthropic_uses_x_api_key_header(monkeypatch):
    monkeypatch.setattr(
        "src.modules.core_connectors.services.base.service_api_key", lambda field: "sk-ant-admin-x"
    )
    headers = AnthropicGateway()._auth_headers()
    assert headers["x-api-key"] == "sk-ant-admin-x"  # не Bearer
    assert headers["anthropic-version"] == "2023-06-01"
    assert "Authorization" not in headers


@pytest.mark.pure
def test_balance_missing_fields_yield_no_metrics():
    assert TavilyGateway()._parse_balance({}).metrics == []
    assert FirecrawlGateway()._parse_balance({}).metrics == []
    assert XaiManagementGateway()._parse_balance({}).metrics == []
    assert OpenRouterGateway()._parse_balance({}).metrics == []


class _StubConnector(ServiceGateway):
    BASE_URL: ClassVar[str] = "https://stub.local"
    API_KEY_FIELD: ClassVar[str] = "stub_api_key"

    def __init__(
        self, *, service: str, enabled: bool = True, has_balance: bool = True, fail: bool = False
    ) -> None:
        super().__init__()
        self.SERVICE = service  # инстанс-атрибуты перекрывают ClassVar — свои значения на стаб
        self.NAME = service.title()
        self.DESCRIPTION = f"stub {service}"
        self.HAS_BALANCE = has_balance
        self._enabled = enabled
        self._fail = fail

    def available(self) -> bool:
        return self._enabled

    async def balance(self) -> ConnectorBalance:
        if not self.HAS_BALANCE:
            return await super().balance()  # база бросит NotImplementedError
        if self._fail:
            raise RuntimeError("boom")
        return ConnectorBalance(
            service=self.SERVICE, name=self.NAME, metrics=[BalanceMetric.money("Баланс", 1.0)]
        )


@pytest.mark.pure
async def test_connector_without_balance_raises():
    with pytest.raises(NotImplementedError):
        await _StubConnector(service="nb", has_balance=False).balance()


@pytest.mark.pure
def test_registry_info_reflects_connector():
    reg = ConnectorsRegistry()
    reg.register(_StubConnector(service="ok", enabled=True, has_balance=True))
    info = reg.info(reg.all()[0])
    assert (info.service, info.name, info.description) == ("ok", "Ok", "stub ok")
    assert info.enabled is True and info.has_balance is True


@pytest.mark.pure
async def test_connectors_without_balance_are_bare_passports():
    reg = ConnectorsRegistry()
    reg.register(_StubConnector(service="ok"))
    views = await reg.connectors(with_balance=False)
    assert len(views) == 1
    assert views[0].info.service == "ok"
    assert views[0].balance is None  # баланс не запрашивали


@pytest.mark.pure
async def test_connectors_with_balance_composes_and_isolates_errors():
    reg = ConnectorsRegistry()
    reg.register(_StubConnector(service="ok", enabled=True))
    reg.register(_StubConnector(service="off", enabled=False))
    reg.register(_StubConnector(service="broken", enabled=True, fail=True))
    reg.register(_StubConnector(service="nobal", has_balance=False))

    views = {v.info.service: v for v in await reg.connectors(with_balance=True)}
    assert views.keys() == {"ok", "off", "broken", "nobal"}  # все коннекторы в списке
    assert views["ok"].balance.metrics[0].amount == 1.0 and views["ok"].balance.error is None
    assert views["off"].balance is None  # отключён → баланс не снимаем
    assert views["broken"].balance.error is not None  # сбой пойман в DTO, сбор не упал
    assert views["nobal"].balance is None  # не умеет баланс → пропущен


@pytest.mark.pure
async def test_connectors_balance_fetched_in_parallel():
    """Балансы снимаются со всех сервисов ПАРАЛЛЕЛЬНО (asyncio.gather), не по очереди.
    Детерминантно, без таймингов: считаем максимум одновременно активных balance()."""
    active = 0
    peak = 0

    class _TrackingConnector(_StubConnector):
        async def balance(self) -> ConnectorBalance:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)  # держим корутину «в работе», давая другим стартовать
            active -= 1
            return ConnectorBalance(service=self.SERVICE, name=self.NAME, metrics=[])

    reg = ConnectorsRegistry()
    for i in range(4):
        reg.register(_TrackingConnector(service=f"s{i}"))

    await reg.connectors(with_balance=True)

    assert peak == 4  # все 4 стартовали до завершения любого → параллельно (последовательно был бы 1)
