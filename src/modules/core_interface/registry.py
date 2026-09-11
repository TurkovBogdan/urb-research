"""Реестр настроек интерфейса: единственное место, где объявлены ключи и умолчания.

О настройке здесь известно три вещи: умолчание (оно же задаёт тип), набор допустимых
значений и предикат для случаев, которые набором не описать. Как настройка выглядит на
экране — подпись, группа, порядок — реестр не знает: интерфейсы собирает фронт, а сервер
остаётся хранилищем, умеющим отказать.

Умолчания в базу не пишутся. Строка появляется только на отклонение, поэтому смена
умолчания здесь доезжает до установки мгновенно: у того, кто настройку не трогал, строки
просто нет, и он читает новое значение.

Карта закрывает пространство ключей: незнакомый ключ отвергается, а не создаёт строку.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from src.modules.core_interface.constants import KEY_MAX_LENGTH, VALUE_MAX_BYTES

TYPE_STRING = "string"
TYPE_NUMBER = "number"
TYPE_BOOLEAN = "boolean"


@dataclass(frozen=True)
class Setting:
    """Объявление настройки: умолчание плюс необязательное ограничение значения."""

    default: Any
    options: tuple[Any, ...] | None = None
    check: Callable[[Any], bool] | None = None


# Приставка ``interface_`` — не проверка (пространство ключей закрывает сама карта), а признак
# принадлежности: по имени видно, отвечает ключ за внешний вид приложения или за что-то другое.
SETTINGS: dict[str, Setting] = {
    "interface_theme": Setting("dark", options=("dark", "light", "system")),
    "interface_font": Setting("onest"),
    "interface_font_reading": Setting("onest"),
    # ``reading`` — не гарнитура, а «как шрифт текста»: заголовки следуют за ним при смене.
    "interface_font_heading": Setting("reading"),
    "interface_font_reading_size": Setting(14, options=(14, 15, 16, 17, 18, 20)),
    "interface_font_reading_weight": Setting(300, options=(100, 200, 300, 400, 500, 600, 700, 800, 900)),
    "interface_font_heading_weight": Setting(600, options=(100, 200, 300, 400, 500, 600, 700, 800, 900)),
    "interface_font_reading_measure": Setting(92, options=(64, 76, 92, 108, 124, 0)),
    "interface_font_mono": Setting("jetbrains-mono"),
    "interface_code_variant": Setting("minimal", options=("icon", "accent", "minimal")),
    "interface_font_code_size": Setting(12, options=(11, 12, 13, 14, 15, 16)),
    "interface_code_line_numbers": Setting(True),
    "interface_font_diagram": Setting("onest"),
    # ``system`` — цвета приложения; остальное — готовые палитры движка схем.
    "interface_diagram_theme": Setting(
        "system",
        options=(
            "system",
            "zinc-light",
            "zinc-dark",
            "github-light",
            "github-dark",
            "tokyo-night",
            "tokyo-night-storm",
            "tokyo-night-light",
            "catppuccin-mocha",
            "catppuccin-latte",
            "nord",
            "nord-light",
            "dracula",
            "solarized-light",
            "solarized-dark",
            "one-dark",
        ),
    ),
    "interface_diagram_align": Setting("left", options=("left", "center")),
    "interface_diagram_max_height": Setting(420, options=(280, 420, 560, 0)),
    "interface_list_research_view": Setting("table", options=("table", "grouped")),
    "interface_nav_document": Setting(True),
    "interface_sidebar_collapsed": Setting(False),
}

_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_registry() -> None:
    """Самопроверка карты на подъёме модуля: кривой ключ роняет старт, а не первый запрос."""
    for key, setting in SETTINGS.items():
        if not _KEY_PATTERN.match(key):
            raise ValueError(f"core_interface: ключ {key!r} не является идентификатором snake_case")
        if len(key) > KEY_MAX_LENGTH:
            raise ValueError(f"core_interface: ключ {key!r} длиннее {KEY_MAX_LENGTH} символов")
        refusal = rejection(key, setting.default)
        if refusal is not None:
            raise ValueError(
                f"core_interface: умолчание {key!r} не проходит собственную проверку — {refusal}"
            )


def rejection(key: str, value: Any) -> str | None:
    """Причина отказа или ``None``, если значение принимается.

    Порядок проверок — от общего к частному: каждая следующая имеет смысл только после
    предыдущей (набор нечего сверять у значения чужого типа).
    """
    setting = SETTINGS.get(key)
    if setting is None:
        return "неизвестная настройка"
    if not matches_default_type(value, setting.default):
        return f"ожидалось значение типа {value_type(setting.default)}"
    if setting.options is not None and value not in setting.options:
        return "значение вне набора допустимых"
    if setting.check is not None and not setting.check(value):
        return "значение не прошло проверку"
    if _serialized_size(value) > VALUE_MAX_BYTES:
        return f"значение длиннее {VALUE_MAX_BYTES} байт"
    return None


def matches_default_type(value: Any, default: Any) -> bool:
    """Тип значения задаёт умолчание — отдельной пометки у настройки нет.

    ``bool`` проверяется первым: в Python он подкласс ``int``, и без явного исключения
    ``True`` прошёл бы как число, а ``1`` — как переключатель.
    """
    if isinstance(default, bool):
        return isinstance(value, bool)
    if isinstance(default, (int, float)):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, str)


def value_type(default: Any) -> str:
    if isinstance(default, bool):
        return TYPE_BOOLEAN
    if isinstance(default, (int, float)):
        return TYPE_NUMBER
    return TYPE_STRING


def schema() -> list[dict[str, Any]]:
    """Машинное описание полей в порядке объявления: тип, умолчание, набор.

    Предикат ``check`` сюда не попадает: он отвечает «да/нет» и данными не описывается.
    Там, где набор должен быть виден человеку, объявляется ``options``.
    """
    return [
        {
            "key": key,
            "type": value_type(setting.default),
            "default": setting.default,
            "options": list(setting.options) if setting.options is not None else None,
        }
        for key, setting in SETTINGS.items()
    ]


def effective_values(stored: Mapping[str, Any]) -> dict[str, Any]:
    """Действующие значения всех полей: умолчание там, где отклонения нет."""
    return {key: stored.get(key, setting.default) for key, setting in SETTINGS.items()}


def unknown_keys(keys: Mapping[str, Any] | list[str]) -> list[str]:
    return [key for key in keys if key not in SETTINGS]


def _serialized_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False).encode())


__all__ = [
    "Setting",
    "SETTINGS",
    "TYPE_BOOLEAN",
    "TYPE_NUMBER",
    "TYPE_STRING",
    "effective_values",
    "matches_default_type",
    "rejection",
    "schema",
    "unknown_keys",
    "validate_registry",
    "value_type",
]
