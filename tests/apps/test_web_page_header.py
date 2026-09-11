"""Стандарт рамки страницы: у каждой вьюхи SPA она есть, и стоит она выше содержимого.

Рамок две, по роду страницы. **Список** открывается шапкой ``PageHeader``: имя раздела там и есть
заголовок страницы, и рамку он несёт сам. **Деталка** рамки не несёт вовсе: липкая колонка живёт
в общем шаблоне ``DetailShell``, который стоит на маршруте-родителе и переживает переход с
артефакта на артефакт — меняется только содержимое справа. Деталка вместо рамки ЗАПОЛНЯЕТ колонку
вызовом ``useDetailRail``, и он же служит здесь признаком её рода.

Общее в обоих случаях одно: рамка — первое, что видно. Стоит странице обойтись без неё (или
поставить её после содержимого), и переход к этой странице читается как прыжок.

Проверка живёт в тестах Python, а не во фронте, по прозаичной причине: тестового раннера у фронта
нет, а договорённость нужна проверяемая. Читаем исходники как текст — ни сборки, ни браузера тут
не нужно, поэтому тест ``pure``. Лежит в ``apps``: это правило про приложение целиком, а не про
отдельный модуль, и так оно попадает в обычный прогон ``--core``.
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

PAGE_FRAME = "<PageHeader"

# Шаблон-рамка деталок: его несёт маршрут-родитель, а не вьюха.
DETAIL_SHELL = WEB_SRC / "layout" / "templates" / "DetailShell.vue"

# Признак деталки: страница заполняет колонку общей рамки вместо того, чтобы рисовать свою.
# Сверяемся с ИМПОРТОМ, а не с вызовом: витрина дизайн-системы показывает тот же вызов строкой
# в примере кода, и по вызову она засчиталась бы деталкой, которой не является.
DETAIL_MARK = "@/layout/detailRail"

# Присутствия рамки мало: она должна стоять ВЫШЕ содержимого, поэтому сверяемся с началом того,
# чем содержимое обычно открывается. Отказ (``SectionError``) сюда не входит — он не содержимое
# страницы, а сообщение вместо него, и на деталке стоит до колонки.
CONTENT_OPENERS = (
    "<VCard",
    "<VDataTable",
    "<VAlert",
    "<section",
    "<SectionHeader",
)


def _template(source: str) -> str:
    """Разметка вьюхи без ``<script>``: в скрипте живут примеры кода витрины дизайн-системы, а в
    них встречается и ``<PageHeader``, и целый ``<template>`` — по ним тест засчитал бы вьюхе
    рамку, которой на странице нет, или принял бы пример за саму разметку. Поэтому скрипт
    вырезается ЦЕЛИКОМ, и только потом ищется шаблон."""
    markup = re.sub(r"<script.*?</script>", "", source, flags=re.S)
    match = re.search(r"<template>(.*)</template>", markup, re.S)
    return match.group(1) if match else ""


def _views() -> list[tuple[str, str]]:
    found = []
    for path in sorted(WEB_SRC.rglob("*View.vue")):
        name = path.relative_to(WEB_SRC).as_posix()
        if name not in EXEMPT:
            found.append((name, path.read_text(encoding="utf-8")))
    return found


def test_every_view_is_covered_by_the_check():
    """Сам обход: если вьюхи перестали находиться, молчаливо зелёный тест хуже отсутствующего."""
    assert len(_views()) > 40


@pytest.mark.parametrize("name,source", _views(), ids=lambda value: value if isinstance(value, str) and value.endswith(".vue") else "")
def test_view_starts_with_its_page_frame(name: str, source: str):
    if DETAIL_MARK in source:
        return

    template = _template(source)
    assert PAGE_FRAME in template, f"{name}: страница без рамки — переход к ней читается как прыжок"

    frame_at = template.index(PAGE_FRAME)
    for opener in CONTENT_OPENERS:
        content_at = template.find(opener)
        if content_at != -1:
            assert frame_at < content_at, f"{name}: рамка стоит ниже содержимого ({opener})"


@pytest.mark.parametrize("name,source", _views(), ids=lambda value: value if isinstance(value, str) and value.endswith(".vue") else "")
def test_detail_page_leaves_the_frame_to_the_shell(name: str, source: str):
    """Деталка не рисует ни колонки, ни шапки: и то и другое принадлежит общей рамке. Своя колонка
    исчезала бы на каждом переходе, а вторая шапка сверху вернула бы ровно то расслоение, ради
    ухода от которого колонку и завели."""
    if DETAIL_MARK not in source:
        return

    template = _template(source)
    for own_frame in ("<PageHeader", "<PageLayout", "<DetailLayout", "<DetailNav"):
        assert own_frame not in template, f"{name}: деталка рисует {own_frame} — рамка задвоена"


def test_detail_shell_carries_the_frame():
    """Рамка деталок одна на всех, и она обязана нести обе части: колонку с выходом и место под
    содержимое. Потеряй шаблон одну из них — со страниц пропал бы выход, и ни один тест выше
    этого бы не заметил: они смотрят на вьюхи, а вьюхи рамки больше не несут."""
    shell = _template(DETAIL_SHELL.read_text(encoding="utf-8"))

    assert "<DetailLayout" in shell, "DetailShell: рамка без колонки"
    assert "<DetailNav" in shell, "DetailShell: колонка без выхода со страницы"
    assert "<RouterView" in shell, "DetailShell: рамке некуда положить содержимое"


def test_exempt_pages_still_exist():
    """Исключения перечислены поимённо: переименовали страницу — правило молча перестало её
    касаться, и это должно упасть здесь, а не всплыть через полгода."""
    for name in EXEMPT:
        assert (WEB_SRC / name).exists(), f"{name}: в списке исключений, но такого файла нет"
