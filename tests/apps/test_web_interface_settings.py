"""Реестр настроек интерфейса и фронт говорят об одном и том же.

Умолчания и наборы допустимых значений объявлены на бэкенде (``core_interface/registry.py``),
но выбор человеку рисует фронт своими списками — с подписями и пояснениями, которых в схеме нет
и не будет. Списки поэтому остаются в ``web/src/constants``, и единственная опасность здесь —
расхождение: набор, разъехавшийся с реестром, означает вариант, который выбирается на экране и
отвергается сервером с 422.

Тест ловит расхождение на прогоне, а не на живом клике. Как и соседние проверки фронта, читает
исходники текстом — ни сборки, ни браузера, поэтому ``pure``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.modules.core_interface.registry import SETTINGS

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"
CONSTANTS = WEB_SRC / "constants"

INTERFACE_PAGE = WEB_SRC / "features" / "settings" / "views" / "InterfaceView.vue"
DOCUMENT_COLUMN = WEB_SRC / "layout" / "components" / "DocumentAppearance.vue"

# Группы страницы настроек, которые повторяет колонка деталки. Четвёртой, «Интерфейс», там нет:
# тема, шрифт интерфейса и раскладка списков к показанному документу отношения не имеют.
DOCUMENT_COLUMN_GROUPS = ("document", "code", "diagram")

# Группа начинается со своей подписи, а поля идут за ней — и на странице (`<SettingsGroup :title>`),
# и в колонке (плашка-заголовок). Поэтому обе поверхности читаются одним разбором. У поля читается
# не только привязка, но и ручка: список с шагом влево-вправо и простой список — разные ручки, и
# выбор между ними принадлежит настройке, а не месту показа.
_GROUP_OR_FIELD = re.compile(
    r"settings\.interface\.group\.(\w+)\.title"
    r"|<(\w+)[^>]*?v-model=\"settings\.([\w.]+)\""
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _numbers(source: str, name: str) -> list[int]:
    body = re.search(rf"{name} = \[([^\]]*)\]", source).group(1)
    return [int(value) for value in re.findall(r"-?\d+", body)]


def _number(source: str, name: str) -> int:
    return int(re.search(rf"{name} = (-?\d+)", source).group(1))


def _string(source: str, name: str) -> str:
    return re.search(rf"{name}(?:: \w+)? = '([^']*)'", source).group(1)


def _codes(source: str, name: str) -> list[str]:
    body = re.search(rf"{name}(?:: [\w\[\]]+)? = \[(.*?)\n\]", source, re.S).group(1)
    return re.findall(r"code: '([^']*)'", body)


def _font_code(source: str, name: str) -> str:
    """``DEFAULT_MONO_FONT = JETBRAINS_MONO.code`` — разворачиваем ссылку до самого кода."""
    option = re.search(rf"{name} = (\w+)\.code", source).group(1)
    return re.search(rf"const {option}: FontOption = \{{\s*code: '([^']*)'", source).group(1)


def _fields_by_group(path: Path) -> dict[str, list[tuple[str, str]]]:
    """Поля «ручка + привязка к стору», разложенные по группам в порядке появления."""
    groups: dict[str, list[tuple[str, str]]] = {}
    current: list[tuple[str, str]] = []
    for match in _GROUP_OR_FIELD.finditer(_source(path)):
        group, control, binding = match.groups()
        if group is not None:
            current = groups.setdefault(group, [])
        else:
            current.append((control, binding))
    return groups


def _options(key: str) -> list:
    return list(SETTINGS[key].options or ())


def _default(key: str):
    return SETTINGS[key].default


def test_store_syncs_exactly_the_keys_the_registry_declares():
    store = _source(WEB_SRC / "stores" / "settings.ts")

    assert set(re.findall(r"synced(?:<[^>]+>)?\('([^']+)'", store)) == set(SETTINGS)


def test_switch_defaults_in_the_store_match_the_registry():
    """У тумблеров умолчание записано литералом в самом сторе — константы у них нет.

    Расхождение здесь тихое и злое: значение, совпавшее с чужим умолчанием, уходит на сервер
    сбросом вместо записи, и настройка возвращается назад на следующей гидрации.
    """
    store = _source(WEB_SRC / "stores" / "settings.ts")
    declared = {
        key: literal == "true"
        for key, literal in re.findall(r"synced\('(\w+)', (true|false), boolCodec\)", store)
    }

    assert declared == {
        key: setting.default
        for key, setting in SETTINGS.items()
        if isinstance(setting.default, bool)
    }


def test_document_column_repeats_the_page_groups_field_for_field():
    """Колонка деталки и страница настроек показывают одни и те же поля одними и теми же ручками.

    Настройка здесь одна на два места (общий стор), поэтому разъехавшиеся наборы означают либо
    поле, которое правится только на странице настроек, либо — что хуже — поле, приписанное в
    колонке к чужой группе: так шрифт кода однажды оказался «оформлением документа». Сверяются и
    порядок (по одной и той же колонке полей глаз ищет знакомое место, а не читает подписи), и
    ручка: список с шагом влево-вправо, подменённый простым списком, отнимает перебор соседних
    вариантов — то самое движение, ради которого настройку и открывают рядом с текстом.
    """
    page = _fields_by_group(INTERFACE_PAGE)

    assert _fields_by_group(DOCUMENT_COLUMN) == {
        group: page[group] for group in DOCUMENT_COLUMN_GROUPS
    }


def test_theme_matches_the_registry():
    theme = _source(CONSTANTS / "theme.ts")

    assert _codes(theme, "THEME_OPTIONS") == _options("interface_theme")
    assert _string(theme, "DEFAULT_THEME") == _default("interface_theme")


def test_reading_zone_matches_the_registry():
    fonts = _source(CONSTANTS / "fonts.ts")

    assert _numbers(fonts, "READING_SIZES") == _options("interface_font_reading_size")
    assert _numbers(fonts, "READING_MEASURES") == _options("interface_font_reading_measure")
    assert _number(fonts, "DEFAULT_READING_SIZE") == _default("interface_font_reading_size")
    assert _number(fonts, "DEFAULT_READING_MEASURE") == _default("interface_font_reading_measure")


def test_font_defaults_match_the_registry():
    fonts = _source(CONSTANTS / "fonts.ts")

    assert _font_code(fonts, "DEFAULT_INTERFACE_FONT") == _default("interface_font")
    assert _font_code(fonts, "DEFAULT_READING_FONT") == _default("interface_font_reading")
    assert _font_code(fonts, "DEFAULT_MONO_FONT") == _default("interface_font_mono")
    assert _font_code(fonts, "DEFAULT_DIAGRAM_FONT") == _default("interface_font_diagram")


def test_diagram_layout_matches_the_registry():
    diagrams = _source(CONSTANTS / "diagrams.ts")

    assert _codes(diagrams, "DIAGRAM_ALIGNS") == _options("interface_diagram_align")
    assert _numbers(diagrams, "DIAGRAM_HEIGHTS") == _options("interface_diagram_max_height")
    assert _string(diagrams, "DEFAULT_DIAGRAM_ALIGN") == _default("interface_diagram_align")
    assert _number(diagrams, "DEFAULT_DIAGRAM_HEIGHT") == _default("interface_diagram_max_height")


def test_research_list_layout_matches_the_registry():
    lists = _source(CONSTANTS / "lists.ts")

    assert _codes(lists, "RESEARCH_LIST_VIEWS") == _options("interface_list_research_view")
    assert _string(lists, "DEFAULT_RESEARCH_LIST_VIEW") == _default("interface_list_research_view")
