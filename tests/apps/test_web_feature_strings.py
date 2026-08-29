"""Строки фич: вьюха просит только те ключи, которые есть в её словаре.

Промах ключа не роняет страницу — `vue-i18n` рисует сам ключ, поэтому в интерфейсе появляется
«research.back.research» вместо подписи, и держится оно ровно до того, как кто-нибудь заметит
глазами. Здесь это падает сразу.

Собираемые по месту ключи (шаблонная строка внутри `t(...)`) не проверяются: их значение
известно только в рантайме.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"
FEATURES = WEB_SRC / "features"


def _features() -> list[str]:
    return sorted(path.name for path in FEATURES.iterdir() if (path / "locales" / "ru.json").exists())


def _value_at(strings: dict, key: str):
    node = strings
    for step in key.split("."):
        if not isinstance(node, dict) or step not in node:
            return None
        node = node[step]
    return node


def test_features_with_strings_are_found():
    assert _features()


@pytest.mark.parametrize("feature", _features(), ids=lambda value: value)
def test_feature_asks_only_for_strings_it_has(feature: str):
    strings = json.loads((FEATURES / feature / "locales" / "ru.json").read_text(encoding="utf-8"))

    missing = set()
    for path in sorted((FEATURES / feature).rglob("*.vue")):
        source = path.read_text(encoding="utf-8")
        for key in re.findall(rf"t\('{feature}\.([\w.-]+)'\)", source):
            if _value_at(strings, key) is None:
                missing.add(f"{path.name}: {feature}.{key}")

    assert not missing, sorted(missing)
