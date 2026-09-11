"""core_connectors: маппинг баланса коннекторов + проверка доступа (``check``).

Маппинг — чистые функции над реальными формами ответов (сверены живьём, см.
`AGENTS/research/xai/INDEX.md` и docstrings коннекторов). Сеть не трогаем: зовём
``_parse_balance`` напрямую, а коннектор поднимаем на пустых значениях доступа —
разбору ответа ключ не нужен.
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from src.core.settings import Field, StrField
from src.modules.core_connectors.access.store import AccessValues
from src.modules.core_connectors.connectors import (
    BUILTIN_CONNECTORS,
    FirecrawlConnector,
    OpenRouterConnector,
    TavilyConnector,
    XaiConnector,
)
from src.modules.core_connectors.connectors.base import Connector, failure_text
from src.modules.core_connectors.connectors.groups import group, groups
from src.modules.core_connectors.connectors.passport import BalanceMetric, ConnectorBalance


def _values(service: str, **values: str) -> AccessValues:
    return AccessValues(access_id=1, service=service, values=values)


def _connector(cls, **values: str):
    return cls(_values(cls.SERVICE, **values))


@pytest.mark.pure
def test_tavily_balance_maps_credits_metric():
    bal = _connector(TavilyConnector)._parse_balance(
        {"account": {"plan_usage": 17, "plan_limit": 1000}}
    )
    assert (bal.service, bal.name) == ("tavily", "Tavily")
    assert len(bal.metrics) == 1
    m = bal.metrics[0]
    assert (m.label, m.unit) == ("Кредиты", "credits")
    assert (m.used, m.total, m.used_percent) == (17, 1000, 1.7)  # 17 / 1000
    assert m.amount is None  # Tavily не в деньгах


@pytest.mark.pure
def test_firecrawl_balance_maps_credits_metric():
    bal = _connector(FirecrawlConnector)._parse_balance(
        {"data": {"remainingCredits": 898, "planCredits": 1000}}
    )
    m = bal.metrics[0]
    assert (m.used, m.total, m.used_percent) == (102, 1000, 10.2)  # planCredits - remaining
    assert m.amount is None


@pytest.mark.pure
def test_xai_balance_negates_total_to_usd_metric():
    # total.val отрицателен при наличии кредита → остаток = -total.val (из центов)
    bal = _connector(XaiConnector)._parse_balance({"total": {"val": "-602"}})
    assert bal.service == "xai"
    m = bal.metrics[0]
    assert (m.label, m.currency) == ("Баланс", "USD")
    assert m.amount == pytest.approx(6.02)
    assert m.used is None and m.total is None


@pytest.mark.pure
async def test_xai_without_management_key_explains_instead_of_failing():
    # Инференс работает без management-ключа — частичная настройка не сбой сервиса
    bal = await _connector(XaiConnector, api_key="k").balance()
    assert bal.metrics == []
    assert "management" in bal.error


@pytest.mark.pure
def test_openrouter_balance_two_metrics():
    raw = {
        "key": {"data": {"usage": 5.16, "limit": 10}},
        "credits": {"data": {"total_credits": 5, "total_usage": 5.16}},
    }
    bal = _connector(OpenRouterConnector)._parse_balance(raw)
    assert bal.service == "openrouter"
    assert [m.label for m in bal.metrics] == ["Лимит ключа", "Баланс"]
    limit, balance = bal.metrics
    assert (limit.used, limit.total, limit.unit, limit.used_percent) == (5.16, 10, "USD", 51.6)
    assert balance.amount == pytest.approx(-0.16)  # total_credits - total_usage, может быть минус


@pytest.mark.pure
def test_openrouter_balance_limit_only_when_no_credits():
    # /credits недоступен (best-effort) → остаётся только метрика лимита ключа
    bal = _connector(OpenRouterConnector)._parse_balance(
        {"key": {"data": {"usage": 1, "limit": 10}}, "credits": None}
    )
    assert [m.label for m in bal.metrics] == ["Лимит ключа"]


@pytest.mark.pure
def test_balance_missing_fields_yield_no_metrics():
    assert _connector(TavilyConnector)._parse_balance({}).metrics == []
    assert _connector(FirecrawlConnector)._parse_balance({}).metrics == []
    assert _connector(XaiConnector)._parse_balance({}).metrics == []
    assert _connector(OpenRouterConnector)._parse_balance({}).metrics == []


class _StubConnector(Connector):
    SERVICE: ClassVar[str] = "stub"
    NAME: ClassVar[str] = "Stub"
    FIELDS: ClassVar[tuple[Field, ...]] = (StrField(key="api_key", label="k", secret=True),)

    def __init__(self, access: AccessValues, *, fail: bool = False, error: str | None = None) -> None:
        super().__init__(access)
        self._fail = fail
        self._error = error

    async def balance(self) -> ConnectorBalance:
        if self._fail:
            raise RuntimeError("boom")
        return ConnectorBalance(
            service=self.SERVICE,
            name=self.NAME,
            metrics=[BalanceMetric.money("Баланс", 1.0)],
            error=self._error,
        )


class _NoBalanceConnector(Connector):
    SERVICE: ClassVar[str] = "nobal"
    NAME: ClassVar[str] = "NoBal"
    HAS_BALANCE: ClassVar[bool] = False


@pytest.mark.pure
async def test_connector_without_balance_raises():
    with pytest.raises(NotImplementedError):
        await _NoBalanceConnector(_values("nobal")).balance()


@pytest.mark.pure
async def test_connector_without_balance_says_so_instead_of_leaking_notimplemented():
    check = await _NoBalanceConnector(_values("nobal")).check()

    assert check.ok is False
    assert "NotImplementedError" not in check.error  # в карточке — ответ, а не имя исключения
    assert "проверка не реализована" in check.error


@pytest.mark.pure
async def test_the_daemon_connector_does_provide_its_own_probe():
    # Инвариант: коннектор без баланса не должен остаться и без пробы
    from src.modules.core_connectors.connectors import WebScrapperConnector

    assert WebScrapperConnector.HAS_BALANCE is False
    assert WebScrapperConnector.check is not Connector.check


@pytest.mark.pure
async def test_check_defaults_to_a_balance_probe():
    check = await _StubConnector(_values("stub")).check()
    assert check.ok is True and check.error is None
    assert check.latency_ms is not None


@pytest.mark.pure
async def test_check_reports_a_failing_call_as_a_diagnosis():
    check = await _StubConnector(_values("stub"), fail=True).check()
    assert check.ok is False
    assert "boom" in check.error  # проверка возвращает диагноз, а не бросает


@pytest.mark.pure
def test_http_failure_is_shortened_to_a_code_and_a_host():
    import httpx

    request = httpx.Request("GET", "https://management-api.x.ai/v1/billing")
    exc = httpx.HTTPStatusError("…", request=request, response=httpx.Response(403, request=request))

    # В карточку идёт код и хост, а не многострочная ссылка на MDN из текста httpx
    assert failure_text(exc) == "HTTP 403 от management-api.x.ai"


@pytest.mark.pure
async def test_check_fails_when_balance_carries_an_error():
    check = await _StubConnector(_values("stub"), error="нет management-ключа").check()
    assert check.ok is False and check.error == "нет management-ключа"


@pytest.mark.pure
def test_access_values_mask_secrets_in_repr():
    values = AccessValues(
        access_id=7,
        service="stub",
        values={"api_key": "super-secret", "base_url": "http://x"},
        secret_keys=frozenset({"api_key"}),
    )
    printed = repr(values)
    assert "super-secret" not in printed  # секрет не утекает через отладочный вывод
    assert "***" in printed and "http://x" in printed


@pytest.mark.pure
def test_secret_keys_come_from_the_passport():
    assert XaiConnector.secret_keys() == {"api_key", "management_api_key"}
    assert TavilyConnector.secret_keys() == {"api_key"}


@pytest.mark.pure
def test_passport_fields_carry_the_partial_configuration_rule():
    # У xAI management-ключ необязателен: без него работает инференс, недоступен лишь баланс
    assert XaiConnector.REQUIRED == ("api_key",)
    assert {f.key for f in XaiConnector.FIELDS} == {"api_key", "management_api_key"}


@pytest.mark.pure
def test_builtin_connectors_stand_in_a_group_of_the_reference():
    # Опечатка в коде группы у встроенного коннектора увела бы карточку в «Прочее» молча
    known = {group.code for group in groups()}
    misplaced = {c.SERVICE: c.GROUP for c in BUILTIN_CONNECTORS if c.GROUP not in known}

    assert misplaced == {}


@pytest.mark.pure
def test_group_reference_is_ordered_and_addressable_by_code():
    assert [g.code for g in groups()] == ["search", "scraping", "models"]
    assert group("scraping").name == "Скрапинг"
    assert group("нет такой") is None
