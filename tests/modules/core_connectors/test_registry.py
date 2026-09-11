"""core_connectors: динамический реестр — регистрация чужого модуля и её правила.

Требование, ради которого реестр вообще динамический: чужой модуль вправе зарегистрировать
свой коннектор после сборки приложения, и он тут же виден в списке — без перезапуска и без
миграции. Перехват чужого кода при этом должен быть невозможен.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from src.core.settings import Field, StrField
from src.modules.core_connectors import service
from src.modules.core_connectors.connectors import BUILTIN_CONNECTORS
from src.modules.core_connectors.connectors.base import Connector
from src.modules.core_connectors.connectors.registry import (
    ConnectorsRegistry,
    connectors_registry,
)
from src.modules.core_connectors.errors import UnknownConnector


class _ForeignConnector(Connector):
    SERVICE: ClassVar[str] = "foreign"
    NAME: ClassVar[str] = "Чужой сервис"
    DESCRIPTION: ClassVar[str] = "Зарегистрирован другим модулем."
    FIELDS: ClassVar[tuple[Field, ...]] = (
        StrField(key="api_key", label="Ключ", secret=True),
        StrField(key="region", label="Регион"),
    )
    REQUIRED: ClassVar[tuple[str, ...]] = ("api_key",)


class _ImpostorConnector(Connector):
    SERVICE: ClassVar[str] = "foreign"
    NAME: ClassVar[str] = "Подмена"


@pytest.fixture
def registry() -> ConnectorsRegistry:
    return ConnectorsRegistry()


@pytest.mark.pure
def test_registration_is_visible_immediately(registry):
    registry.register(_ForeignConnector, owner="other_module")

    assert registry.services() == ["foreign"]
    assert registry.get("foreign") is _ForeignConnector
    assert registry.owner("foreign") == "other_module"


@pytest.mark.pure
def test_passport_describes_the_fields_without_values(registry):
    registry.register(_ForeignConnector, owner="other_module")

    passport = registry.passport("foreign")

    assert (passport.name, passport.owner) == ("Чужой сервис", "other_module")
    assert passport.group == ""  # группу коннектор вправе не объявлять — это «Прочее»
    assert [f["key"] for f in passport.fields] == ["api_key", "region"]
    assert passport.fields[0]["secret"] is True
    assert "is_set" not in passport.fields[0]  # заполненность — свойство записи, не паспорта


@pytest.mark.pure
def test_taking_over_a_registered_code_is_refused(registry):
    registry.register(_ForeignConnector, owner="other_module")

    with pytest.raises(ValueError):
        registry.register(_ImpostorConnector, owner="attacker_module")


@pytest.mark.pure
def test_repeated_identical_registration_is_a_no_op(registry):
    registry.register(_ForeignConnector, owner="other_module")
    registry.register(_ForeignConnector, owner="other_module")  # пересборка приложения

    assert registry.services() == ["foreign"]


@pytest.mark.pure
def test_only_the_owner_may_unregister(registry):
    registry.register(_ForeignConnector, owner="other_module")

    with pytest.raises(ValueError):
        registry.unregister("foreign", owner="attacker_module")

    registry.unregister("foreign", owner="other_module")
    assert registry.services() == []


@pytest.mark.pure
def test_unknown_connector_is_a_typed_error(registry):
    with pytest.raises(UnknownConnector):
        registry.get("nope")


@pytest.mark.pure
def test_builtins_are_registered_by_the_module_itself():
    # Реестр полон и вне поднятого приложения: встроенные вносятся импортом пакета
    assert set(connectors_registry.services()) >= {c.SERVICE for c in BUILTIN_CONNECTORS}
    assert connectors_registry.owner("tavily") == "core_connectors"


@pytest.mark.pure
def test_every_builtin_connector_is_registered():
    # Инвариант: коннектор из дерева либо в реестре, либо его вообще нет —
    # «умеет баланс» членством в реестре больше не управляет
    for connector in BUILTIN_CONNECTORS:
        assert connectors_registry.get(connector.SERVICE) is connector


@pytest.mark.pure
def test_builtin_passports_declare_only_string_fields():
    # Значения записи едут по HTTP как dict[str, str] и так же лежат в колонке: поле другого
    # типа потребует разбора через field.parse() на входе и выходе. Пока такого поля нет —
    # этот тест и есть напоминание, что его появление стоит той работы
    for connector in BUILTIN_CONNECTORS:
        kinds = {field.kind for field in connector.FIELDS}
        assert kinds <= {"str"}, f"{connector.SERVICE}: не-строковые поля {kinds}"


@pytest.mark.pure
def test_required_fields_belong_to_the_passport():
    # Опечатка в REQUIRED сделала бы запись вечно «не настроенной» без объяснимой причины
    for connector in BUILTIN_CONNECTORS:
        keys = {field.key for field in connector.FIELDS}
        assert set(connector.REQUIRED) <= keys, connector.SERVICE


@pytest.mark.pure
def test_a_connector_without_balance_still_belongs_to_the_registry():
    scrapper = connectors_registry.get("web_scrapper")

    assert scrapper.HAS_BALANCE is False
    assert scrapper in connectors_registry.all()


@pytest.mark.db
async def test_record_survives_unregistration_of_its_connector(db):
    connectors_registry.register(_ForeignConnector, owner="other_module")
    try:
        row = await service.create_access(connector="foreign", values={"api_key": "sk-1"})
    finally:
        connectors_registry.unregister("foreign", owner="other_module")

    rows = await service.access_rows()

    assert [r.id for r in rows] == [row.id]  # строка на месте, значения не потеряны
    assert rows[0].connector_name == ""  # коннектор неизвестен — так и показываем
    assert rows[0].status.status != "ok"


@pytest.mark.db
async def test_a_connector_registered_later_is_configurable_at_once(db):
    connectors_registry.register(_ForeignConnector, owner="other_module")
    try:
        assert "foreign" in [p.service for p in service.passports()]
        row = await service.create_access(
            connector="foreign", values={"api_key": "sk-1", "region": "eu"}
        )
        assert row.status.status == "ok"
    finally:
        connectors_registry.unregister("foreign", owner="other_module")
