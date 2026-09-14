"""Форма папки модуля фронта: все папки под ``web/src/features/`` устроены одинаково.

Договорённость сложилась сама — вход в модуль (``api.ts`` + ``routes.ts`` + ``views/``), свой
словарь строк (``locales/ru.json``, он же namespace модуля в ``plugins/i18n.ts``), композаблы в
``composables/`` и единственное имя для файла, переводящего коды бэка в подписи (``labels.ts``).
Пока она нигде не записана, следующая папка заводится на глаз, и расхождение замечают уже при
переезде модуля.

Проверка живёт в тестах Python, а не во фронте, по той же причине, что и стандарт рамки страницы
(``test_web_page_header.py``): тестового раннера у фронта нет, а договорённость нужна проверяемая.
Читаем дерево файлов — ни сборки, ни браузера тут не нужно, поэтому тест ``pure``. Лежит в
``apps``: правило про приложение целиком, а не про отдельный модуль, и так оно попадает в обычный
прогон ``--core``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"
FEATURES = WEB_SRC / "features"

ENTRY_POINTS = ("api.ts", "routes.ts", "views")

# Словарь модуля подключается по имени папки (`import.meta.glob` в `plugins/i18n.ts`), поэтому
# папка без него не просто «без перевода» — у её строк нет и места, куда их положить.
DICTIONARY = "locales/ru.json"


def _modules() -> list[str]:
    return sorted(path.name for path in FEATURES.iterdir() if path.is_dir())


def test_modules_are_found():
    """Сам обход: если папки перестали находиться, молчаливо зелёный тест хуже отсутствующего."""
    assert len(_modules()) > 5


@pytest.mark.parametrize("module", _modules(), ids=lambda value: value)
def test_module_has_its_entry_points(module: str):
    for entry in ENTRY_POINTS:
        assert (FEATURES / module / entry).exists(), f"{module}: нет {entry}"


@pytest.mark.parametrize("module", _modules(), ids=lambda value: value)
def test_module_has_its_dictionary(module: str):
    assert (FEATURES / module / DICTIONARY).exists(), (
        f"{module}: нет {DICTIONARY} — строки модуля остались литералами в разметке"
    )


@pytest.mark.parametrize("module", _modules(), ids=lambda value: value)
def test_composables_live_in_their_folder(module: str):
    at_root = sorted(path.name for path in (FEATURES / module).glob("use*.ts"))
    assert not at_root, f"{module}: композаблы лежат в корне папки, место им в composables/: {at_root}"


@pytest.mark.parametrize("module", _modules(), ids=lambda value: value)
def test_label_mapping_is_named_labels(module: str):
    """Перевод кодов бэка в подписи — одна и та же работа во всех модулях, и имя у файла одно:
    ``labels.ts``. Своё имя в каждом модуле (``groupText`` / ``taskText`` / ``settingText``)
    прятало общий приём: искать его приходилось по содержимому, а не по имени."""
    misnamed = sorted(path.name for path in (FEATURES / module).glob("*Text.ts"))
    assert not misnamed, f"{module}: файл подписей назван не labels.ts: {misnamed}"
