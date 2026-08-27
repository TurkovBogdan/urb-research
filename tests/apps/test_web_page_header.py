"""Стандарт шапки страницы: каждая вьюха SPA начинается с ``PageHeader``.

Проверка живёт в тестах Python, а не во фронте, по прозаичной причине: тестового раннера у фронта
нет, а договорённость нужна проверяемая. Читаем исходники как текст — ни сборки, ни браузера тут
не нужно, поэтому тест ``pure``. Лежит в ``apps``: это правило про приложение целиком, а не про
отдельный модуль, и так оно попадает в обычный прогон ``--core``.

Правило: единый вид шапки на всех страницах — это то, за что цепляется глаз при переходе между
ними. Стоит одной странице обойтись без шапки (или поставить её после содержимого), и переход к
ней читается как прыжок. Наглядно анатомия разобрана в дизайн-системе (``/design-system/page-header``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"

# Страницы без шапки — только те, у которых нет и самой страничной рамки:
# главная (витрина-приветствие во весь экран) и экран «не найдено» (он рисует себя сам).
EXEMPT = {
    "views/HomeView.vue",
    "views/errors/NotFoundView.vue",
}

# Первое, что видно на странице, — шапка. Присутствия мало: она должна стоять ВЫШЕ содержимого,
# поэтому сверяемся с началом того, чем содержимое обычно открывается.
CONTENT_OPENERS = (
    "<VCard",
    "<VDataTable",
    "<VAlert",
    "<section",
    "<SectionHeader",
    "<SectionError",
)


def _template(source: str) -> str:
    """Разметка вьюхи без ``<script>``: в скрипте ``<PageHeader`` встречается внутри сниппетов
    дизайн-системы, и по нему тест засчитал бы шапку, которой на странице нет."""
    match = re.search(r"<template>(.*)</template>", source, re.S)
    return match.group(1) if match else ""


def _views() -> list[tuple[str, str]]:
    found = []
    for path in sorted(WEB_SRC.rglob("*View.vue")):
        name = path.relative_to(WEB_SRC).as_posix()
        if name not in EXEMPT:
            found.append((name, _template(path.read_text(encoding="utf-8"))))
    return found


def test_every_view_is_covered_by_the_check():
    """Сам обход: если вьюхи перестали находиться, молчаливо зелёный тест хуже отсутствующего."""
    assert len(_views()) > 40


@pytest.mark.parametrize("name,template", _views(), ids=lambda value: value if isinstance(value, str) and value.endswith(".vue") else "")
def test_view_starts_with_the_page_header(name: str, template: str):
    assert "<PageHeader" in template, f"{name}: страница без шапки — переход к ней читается как прыжок"

    header_at = template.index("<PageHeader")
    for opener in CONTENT_OPENERS:
        content_at = template.find(opener)
        if content_at != -1:
            assert header_at < content_at, f"{name}: шапка стоит ниже содержимого ({opener})"


def test_exempt_pages_still_exist():
    """Исключения перечислены поимённо: переименовали страницу — правило молча перестало её
    касаться, и это должно упасть здесь, а не всплыть через полгода."""
    for name in EXEMPT:
        assert (WEB_SRC / name).exists(), f"{name}: в списке исключений, но такого файла нет"
