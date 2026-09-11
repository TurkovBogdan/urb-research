"""core_interface: реестр — самосогласованность карты и правила отказа."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from src.modules.core_interface import registry
from src.modules.core_interface.module import CoreInterfaceModule
from src.modules.core_interface.constants import KEY_MAX_LENGTH, VALUE_MAX_BYTES
from src.modules.core_interface.registry import Setting

pytestmark = pytest.mark.pure


def test_registry_is_self_consistent():
    registry.validate_registry()


def test_every_setting_declared_today_is_about_appearance():
    assert all(key.startswith("interface_") for key in registry.SETTINGS)


def test_broken_key_fails_the_startup_check(monkeypatch):
    monkeypatch.setitem(registry.SETTINGS, "Interface.Theme", Setting("dark"))

    with pytest.raises(ValueError, match="snake_case"):
        registry.validate_registry()


def test_too_long_key_fails_the_startup_check(monkeypatch):
    monkeypatch.setitem(registry.SETTINGS, "i" * (KEY_MAX_LENGTH + 1), Setting("dark"))

    with pytest.raises(ValueError, match="длиннее"):
        registry.validate_registry()


def test_default_outside_its_own_options_fails_the_startup_check(monkeypatch):
    monkeypatch.setitem(registry.SETTINGS, "interface_theme", Setting("plaid", options=("dark",)))

    with pytest.raises(ValueError, match="умолчание"):
        registry.validate_registry()


def test_broken_registry_stops_the_build(monkeypatch, config):
    """Проверка висит на ``configure``, а не на ``on_startup``: исключения второго lifespan
    ловит и пишет в лог, и кривая карта уехала бы в установку молча."""
    monkeypatch.setitem(registry.SETTINGS, "Interface.Theme", Setting("dark"))

    with pytest.raises(ValueError):
        CoreInterfaceModule().configure(FastAPI(), config)


def test_unknown_key_is_rejected():
    assert registry.rejection("interface_nope", "dark") == "неизвестная настройка"


def test_boolean_is_not_a_number_and_a_number_is_not_a_boolean():
    assert registry.rejection("interface_nav_document", 1) is not None
    assert registry.rejection("interface_font_reading_size", True) is not None


def test_value_outside_the_option_set_is_rejected():
    assert registry.rejection("interface_font_reading_size", 19) == "значение вне набора допустимых"
    assert registry.rejection("interface_theme", "plaid") == "значение вне набора допустимых"


def test_reading_weight_takes_the_css_ladder_by_hundreds():
    assert registry.SETTINGS["interface_font_reading_weight"].default == 300
    assert registry.rejection("interface_font_reading_weight", 900) is None
    assert registry.rejection("interface_font_reading_weight", 350) == "значение вне набора допустимых"


def test_code_size_is_its_own_ladder_below_the_reading_one():
    assert registry.SETTINGS["interface_font_code_size"].default == 12
    assert registry.rejection("interface_font_code_size", 11) is None
    assert registry.rejection("interface_font_code_size", 20) == "значение вне набора допустимых"


def test_heading_font_defaults_to_the_reading_one():
    assert registry.SETTINGS["interface_font_heading"].default == "reading"
    assert registry.rejection("interface_font_heading", "literata") is None


def test_heading_weight_stands_above_the_text_by_default():
    assert registry.SETTINGS["interface_font_heading_weight"].default == 600
    assert registry.rejection("interface_font_heading_weight", 100) is None
    assert registry.rejection("interface_font_heading_weight", 650) == "значение вне набора допустимых"


def test_failing_predicate_is_rejected(monkeypatch):
    monkeypatch.setitem(
        registry.SETTINGS, "interface_font", Setting("onest", check=lambda value: value == "onest")
    )

    assert registry.rejection("interface_font", "golos") == "значение не прошло проверку"


def test_oversized_value_is_rejected():
    assert registry.rejection("interface_font", "x" * (VALUE_MAX_BYTES + 1)) is not None


def test_font_and_sort_keys_are_limited_by_type_alone():
    assert registry.rejection("interface_font", "any-family-we-ship-later") is None


def test_schema_describes_every_field_in_declaration_order():
    schema = registry.schema()

    assert [field["key"] for field in schema] == list(registry.SETTINGS)
    by_key = {field["key"]: field for field in schema}
    assert by_key["interface_theme"] == {
        "key": "interface_theme",
        "type": "string",
        "default": "dark",
        "options": ["dark", "light", "system"],
    }
    assert by_key["interface_nav_document"]["type"] == "boolean"
    assert by_key["interface_font_reading_size"]["type"] == "number"
    assert by_key["interface_font"]["options"] is None


def test_effective_values_fill_untouched_keys_with_defaults():
    values = registry.effective_values({"interface_theme": "light"})

    assert values["interface_theme"] == "light"
    assert values["interface_font_reading_size"] == 14
    assert values.keys() == registry.SETTINGS.keys()
