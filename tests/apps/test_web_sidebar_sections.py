"""Разделы бокового меню: у каждого есть код, и запись меню называет свой раздел этим кодом.

Раньше раздел был просто подписью в плоском списке, и место записи задавалось соседством строк.
Теперь запись объявляет раздел (``section: '<код>'``) — а это значит, что опечатка в коде уводит
запись в несуществующий раздел, и в меню она просто не появится: ни сборка, ни типы такого не
ловят, код раздела для них обычная строка. Второй молчаливый отказ — подпись: раздел рисуется
через ``t(labelKey)``, и ключ без перевода выводится в меню как есть, путём ключа.

Проверка живёт в тестах Python по той же причине, что и соседние: тестового раннера у фронта нет,
а договорённость нужна проверяемая. Исходники читаются как текст, поэтому тест ``pure``; лежит в
``apps``, так как правило про оболочку приложения целиком.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"

SIDEBAR = WEB_SRC / "layout" / "components" / "AppSidebar.vue"
COMMON_LOCALE = WEB_SRC / "locales" / "ru.json"

# Подписи разделов — общие для оболочки, а не для модуля, поэтому живут в общем словаре.
SECTION_LABEL_NAMESPACE = "common.nav."


def _array_literal(name: str) -> str:
    """Тело массива ``const <name> … = [ … ]``. Закрывающая скобка ищется в начале строки: внутри
    записи есть вложенный массив ``children``, и его ``],`` стоит с отступом."""
    source = SIDEBAR.read_text(encoding="utf-8")
    match = re.search(rf"const {name}[^=]*= \[(.*?)\n\]", source, re.S)
    assert match, f"{name}: массив не найден — тест смотрит не туда"
    return match.group(1)


def _declared_sections() -> dict[str, str]:
    """Код раздела → ключ его подписи. Поля читаются порознь, а не парой: порядок их внутри записи
    — дело вкуса, и тест, привязанный к нему, обвинил бы в поломке записи меню вместо разделов."""
    sections = {}
    for entry in re.findall(r"\{[^{}]*\}", _array_literal("navSections")):
        code = re.search(r"code: '([^']+)'", entry)
        label_key = re.search(r"labelKey: '([^']+)'", entry)
        if code and label_key:
            sections[code.group(1)] = label_key.group(1)
    return sections


def _sections_named_by_entries() -> list[str]:
    return re.findall(r"section: '([^']+)'", _array_literal("navEntries"))


def _common_messages() -> dict:
    return json.loads(COMMON_LOCALE.read_text(encoding="utf-8"))


def test_the_menu_is_actually_parsed():
    """Молчаливо зелёный тест хуже отсутствующего: если регулярка перестала видеть списки, упасть
    должно здесь, а не через полгода пустым меню."""
    assert len(_declared_sections()) >= 5
    assert len(_sections_named_by_entries()) >= 5


@pytest.mark.parametrize("section", sorted(set(_sections_named_by_entries())), ids=lambda value: value)
def test_entry_names_a_declared_section(section: str):
    assert section in _declared_sections(), f"{section}: запись меню в незаявленном разделе — не покажется"


@pytest.mark.parametrize("code,label_key", sorted(_declared_sections().items()), ids=lambda value: value)
def test_section_label_resolves(code: str, label_key: str):
    assert label_key.startswith(SECTION_LABEL_NAMESPACE), (
        f"{code}: подпись раздела берётся из общего словаря, ключ должен быть {SECTION_LABEL_NAMESPACE}*"
    )

    messages = _common_messages()
    for key in label_key.removeprefix("common.").split("."):
        assert isinstance(messages, dict) and key in messages, f"{code}: нет перевода для {label_key}"
        messages = messages[key]

    assert isinstance(messages, str) and messages, f"{code}: перевод {label_key} пуст"
