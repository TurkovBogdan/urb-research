"""core_connectors: бюджет опроса — таймаут вызова и общий дедлайн выдачи.

Дефект, ради которого это писалось: без бюджета одного медленного сервиса хватает, чтобы
положить всю страницу. Проверяем, что медленный и падающий коннекторы остаются ошибкой
**в своей карточке**, а соседние отдаются как есть.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

import pytest

from src.core.settings import Field, StrField
from src.modules.core_connectors import service, settings
from src.modules.core_connectors.connectors.base import Connector
from src.modules.core_connectors.connectors.passport import BalanceMetric, ConnectorBalance
from src.modules.core_connectors.connectors.registry import connectors_registry

pytestmark = pytest.mark.db

_FIELDS: tuple[Field, ...] = (StrField(key="api_key", label="Ключ", secret=True),)


class _FastConnector(Connector):
    SERVICE: ClassVar[str] = "fast_stub"
    NAME: ClassVar[str] = "Быстрый"
    FIELDS: ClassVar[tuple[Field, ...]] = _FIELDS
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)

    async def balance(self) -> ConnectorBalance:
        return ConnectorBalance(
            service=self.SERVICE, name=self.NAME, metrics=[BalanceMetric.money("Баланс", 7.0)]
        )


class _SlowConnector(Connector):
    SERVICE: ClassVar[str] = "slow_stub"
    NAME: ClassVar[str] = "Медленный"
    FIELDS: ClassVar[tuple[Field, ...]] = _FIELDS
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)

    async def balance(self) -> ConnectorBalance:
        await asyncio.sleep(30)
        raise AssertionError("до сюда дойти не должно — вызов обязан упереться в бюджет")


class _BrokenConnector(Connector):
    SERVICE: ClassVar[str] = "broken_stub"
    NAME: ClassVar[str] = "Сломанный"
    FIELDS: ClassVar[tuple[Field, ...]] = _FIELDS
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)

    async def balance(self) -> ConnectorBalance:
        raise RuntimeError("boom")


class _NoBalanceConnector(Connector):
    SERVICE: ClassVar[str] = "nobal_stub"
    NAME: ClassVar[str] = "Без баланса"
    HAS_BALANCE: ClassVar[bool] = False
    FIELDS: ClassVar[tuple[Field, ...]] = _FIELDS


@pytest.fixture
def stub_connectors():
    """Зарегистрировать стабы на время теста и обязательно снять их после."""
    stubs = (_FastConnector, _SlowConnector, _BrokenConnector, _NoBalanceConnector)
    for connector in stubs:
        connectors_registry.register(connector, owner="test")
    try:
        yield stubs
    finally:
        for connector in stubs:
            connectors_registry.unregister(connector.SERVICE, owner="test")


async def _seed(*services: str) -> None:
    for name in services:
        await service.create_access(connector=name, values={"api_key": "k"})


async def test_a_slow_connector_does_not_hold_the_whole_page(db, stub_connectors, monkeypatch):
    monkeypatch.setattr(settings, "poll_deadline", lambda: 0.05)
    monkeypatch.setattr(settings, "balance_timeout", lambda: 30)
    await _seed("fast_stub", "slow_stub")

    views = {v.connector: v for v in await service.access_views(with_balance=True)}

    assert views["fast_stub"].balance.metrics[0].amount == 7.0  # сосед отдан как есть
    assert views["slow_stub"].balance.error == "Превышен дедлайн опроса"
    assert views["slow_stub"].status.status == "error"


async def test_a_call_is_capped_by_its_own_timeout(db, stub_connectors, monkeypatch):
    monkeypatch.setattr(settings, "balance_timeout", lambda: 0.05)
    await _seed("slow_stub")

    balance = await service.access_balance((await service.access_rows())[0].id)

    assert balance.error == "Превышен дедлайн опроса"
    assert balance.metrics == []


async def test_a_failing_connector_stays_an_error_in_its_own_card(db, stub_connectors):
    await _seed("fast_stub", "broken_stub")

    views = {v.connector: v for v in await service.access_views(with_balance=True)}

    assert views["fast_stub"].status.status == "ok"
    assert "boom" in views["broken_stub"].balance.error
    assert views["broken_stub"].status.status == "error"


async def test_balance_is_not_polled_where_it_cannot_be(db, stub_connectors):
    await _seed("nobal_stub")
    await service.create_access(connector="fast_stub", values={})  # не заполнен

    views = {v.connector: v for v in await service.access_views(with_balance=True)}

    assert views["nobal_stub"].has_balance is False and views["nobal_stub"].balance is None
    assert views["fast_stub"].status.status == "unconfigured"
    assert views["fast_stub"].balance is None  # неготовую запись в сеть не тащим


async def test_check_is_capped_by_the_same_timeout(db, stub_connectors, monkeypatch):
    monkeypatch.setattr(settings, "balance_timeout", lambda: 0.05)
    await _seed("slow_stub")

    check = await service.check_access((await service.access_rows())[0].id)

    assert check.ok is False and check.error == "Превышен дедлайн опроса"
