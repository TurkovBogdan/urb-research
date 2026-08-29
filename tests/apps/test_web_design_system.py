"""Витрина дизайн-системы: у каждой страницы есть и вьюха, и её строки.

Страница витрины регистрируется в трёх местах сразу — маршрут, плитка в индексе, словарь. Забыть
одно из трёх легко, и промах словаря молчит: `vue-i18n` рисует сам ключ, то есть страница
открывается и выглядит почти нормально. Поэтому связка проверяется здесь.

Читаем исходники как текст — ни сборки, ни браузера, поэтому тест ``pure``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"
ROUTES = WEB_SRC / "router" / "design-system.ts"
INDEX_VIEW = WEB_SRC / "views" / "design-system" / "DesignSystemIndexView.vue"
STRINGS = WEB_SRC / "locales" / "design-system" / "ru.json"


def _pages() -> list[tuple[str, str]]:
    """``slug → путь вьюхи`` из таблицы ``PAGES`` маршрутизатора витрины."""
    table = re.search(r"const PAGES[^{]*\{(.*?)\n\}", ROUTES.read_text(encoding="utf-8"), re.S)
    assert table, "таблица страниц витрины не найдена — тест ниже стал бы молчаливо зелёным"
    return re.findall(r"^\s*'?([\w-]+)'?:\s*'([\w/]+)',", table.group(1), re.M)


def _strings() -> dict:
    return json.loads(STRINGS.read_text(encoding="utf-8"))


def test_pages_are_found():
    assert len(_pages()) > 20


@pytest.mark.parametrize("slug,view", _pages(), ids=lambda value: value)
def test_page_has_its_view(slug: str, view: str):
    assert (WEB_SRC / "views" / "design-system" / f"{view}.vue").exists()


@pytest.mark.parametrize("slug,view", _pages(), ids=lambda value: value)
def test_page_has_its_strings(slug: str, view: str):
    strings = _strings()
    tile = strings["index"]["page"].get(slug)
    page = strings["page"].get(slug)

    assert tile and tile.get("label"), f"{slug}: плитка витрины без подписи"
    assert page and page.get("title") and page.get("description"), f"{slug}: страница без имени"


@pytest.mark.parametrize("slug,view", _pages(), ids=lambda value: value)
def test_page_is_listed_on_the_index(slug: str, view: str):
    """Маршрут без плитки — страница, до которой не дойти иначе как по прямой ссылке."""
    assert f"slug: '{slug}'" in INDEX_VIEW.read_text(encoding="utf-8")


def _value_at(strings: dict, key: str):
    node = strings
    for step in key.split("."):
        if not isinstance(node, dict) or step not in node:
            return None
        node = node[step]
    return node


@pytest.mark.parametrize("slug,view", _pages(), ids=lambda value: value)
def test_page_asks_only_for_strings_it_has(slug: str, view: str):
    """Промах ключа не роняет страницу — `vue-i18n` рисует сам ключ, и текст «section.rule_note»
    посреди витрины замечают в лучшем случае через неделю. Собираемые по месту ключи (шаблонная
    строка внутри `t(...)`) сюда не попадают — их значение известно только в рантайме."""
    source = (WEB_SRC / "views" / "design-system" / f"{view}.vue").read_text(encoding="utf-8")
    strings = _strings()

    for key in re.findall(r"t\('design-system\.([\w.-]+)'\)", source):
        assert _value_at(strings, key) is not None, f"{view}: нет строки design-system.{key}"
