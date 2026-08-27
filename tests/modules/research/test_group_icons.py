"""research: палитра иконок группы (``icons.py``) — снимок набора + парность с реестром фронта."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.modules.research.icons import GROUP_ICONS, group_icons

_FRONT_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "web/src/features/research/constants/groupIcons.ts"
)

pytestmark = pytest.mark.pure


def test_palette_is_a_deduplicated_snapshot():
    palette = group_icons()

    assert len(palette) == 120
    assert len(set(palette)) == len(palette)
    assert palette == list(GROUP_ICONS)


def test_names_are_tabler_kebab():
    """Имена — kebab без префикса ``Icon``: так их печатает каталог tabler и ждёт реестр фронта."""
    assert all(name == name.lower() for name in GROUP_ICONS)
    assert all(name.strip("-") == name for name in GROUP_ICONS)
    assert not any(" " in name or "_" in name for name in GROUP_ICONS)


def test_front_registry_covers_exactly_the_palette():
    """Половинки контракта не должны разъезжаться: имя без импорта на фронте не нарисуется.

    Тест читает TS-реестр как текст: это единственный шов между двумя языками, и молчаливое
    расхождение здесь выглядит как «иконка почему-то стала папкой».
    """
    registry = _FRONT_REGISTRY.read_text(encoding="utf-8")
    mapped = re.findall(r"^  '([a-z0-9-]+)': (Icon\w+),$", registry, re.M)

    assert [name for name, _ in mapped] == list(GROUP_ICONS)
    assert len({component for _, component in mapped}) == len(mapped)


def test_palette_is_immutable_and_copied_out():
    """``group_icons()`` отдаёт копию — правка ответа не портит константу."""
    assert isinstance(GROUP_ICONS, tuple)

    palette = group_icons()
    palette.append("junk")

    assert "junk" not in group_icons()
