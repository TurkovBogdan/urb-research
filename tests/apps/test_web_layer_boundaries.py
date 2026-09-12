"""Направление зависимостей в SPA: фундамент не знает про модули, а модули — друг про друга.

``web/src`` делится на два яруса с ПРОТИВОПОЛОЖНЫМ направлением связи. **Фундамент** (``api``,
``shared``, ``components``, ``composables``, ``constants``, ``stores``, ``layout``) — то, что
модули импортируют; сам он про них не знает. **Композиция** (``router``, ``plugins``, ``views``) —
наоборот, собирает модули воедино. Слой, попавший в оба списка, — это цикл: правка модуля
потянула бы за собой оболочку, которая этот же модуль и грузит.

Отсюда и правило про общий компонент: у компонента с одним потребителем дом внутри его модуля, а
переезд в фундамент разрешён со второго потребителя — и только вместе с отказом от доменного типа.

Композиция намеренно вне проверки, и это не упущение: ``plugins/i18n.ts`` находит словари модулей
глобом, а витрина дизайн-системы (``views/design-system``) до сих пор тянется в ``research`` —
отдельная работа, уже выделенная в свою.

Проверка живёт в тестах Python по той же причине, что и рамка страницы (см.
``test_web_page_header.py``): тестового раннера у фронта нет, а договорённость нужна проверяемая.
Читаем исходники как текст — ни сборки, ни браузера, поэтому тест ``pure``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"

FOUNDATION = ("api", "shared", "components", "composables", "constants", "stores", "layout")
MODULES_ROOT = WEB_SRC / "features"

SOURCE_SUFFIXES = (".ts", ".vue")

# Статический `from '…'`, побочный `import '…'` и ленивый `import('…')` — все три формы несут
# зависимость, и мимо любой из них правило утекло бы.
SPECIFIER = re.compile(r"""(?:from|import)\s*\(?\s*['"]([^'"]+)['"]""")


def _sources(root: Path) -> list[tuple[str, str]]:
    found = []
    for path in sorted(root.rglob("*")):
        if path.suffix in SOURCE_SUFFIXES:
            found.append((path.relative_to(WEB_SRC).as_posix(), path.read_text(encoding="utf-8")))
    return found


def _foundation_sources() -> list[tuple[str, str]]:
    return [source for layer in FOUNDATION for source in _sources(WEB_SRC / layer)]


def _module_sources() -> list[tuple[str, str]]:
    return _sources(MODULES_ROOT)


def _imported_paths(name: str, source: str) -> list[str]:
    """Куда указывают импорты файла, в координатах ``web/src``.

    Псевдоним и относительный путь считаются одинаково: иначе `../../<чужой модуль>` обходил бы
    правило молча, оставляя зелёный тест при живом нарушении. Имя пакета (ни `@/`, ни точки) — не
    наш случай.
    """
    here = (WEB_SRC / name).parent
    inside_web_src = []
    for specifier in SPECIFIER.findall(source):
        if specifier.startswith("@/"):
            target = WEB_SRC / specifier[2:]
        elif specifier.startswith("."):
            target = (here / specifier).resolve()
        else:
            continue
        if target.is_relative_to(WEB_SRC):
            inside_web_src.append(target.relative_to(WEB_SRC).as_posix())
    return inside_web_src


def _module_of(path: str) -> str | None:
    parts = path.split("/")
    return parts[1] if parts[0] == "features" and len(parts) > 1 else None


def _case_id(value: str) -> str:
    """Имя случая — путь файла; вторым элементом пары идёт его исходник, и в имя он не годится:
    многострочный текст уехал бы целиком в каждый идентификатор узла."""
    return "" if "\n" in value else value


def test_both_tiers_are_actually_walked():
    """Молчаливо зелёный тест хуже отсутствующего: переехал каталог — падаем здесь."""
    assert len(_foundation_sources()) > 80
    assert len(_module_sources()) > 60


@pytest.mark.parametrize(
    "name,source",
    _foundation_sources(),
    ids=_case_id,
)
def test_foundation_does_not_import_a_module(name: str, source: str):
    for imported in _imported_paths(name, source):
        assert _module_of(imported) is None, (
            f"{name}: фундамент тянется в модуль ({imported}) — оболочку уже не собрать без него"
        )


@pytest.mark.parametrize(
    "name,source",
    _module_sources(),
    ids=_case_id,
)
def test_a_module_does_not_import_another_module(name: str, source: str):
    own = _module_of(name)
    for imported in _imported_paths(name, source):
        other = _module_of(imported)
        assert other in (None, own), (
            f"{name}: модуль тянется в модуль ({imported}) — общее место им обоим в фундаменте"
        )
