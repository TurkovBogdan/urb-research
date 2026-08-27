"""research: палитра цветов группы (``colors.py``) — снимок набора + парность с реестром фронта."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.modules.research.colors import GROUP_COLORS, group_colors
from src.modules.research.constants import GROUP_COLOR_MAX

_FRONT_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "web/src/features/research/constants/groupColors.ts"
)

pytestmark = pytest.mark.pure


def test_palette_is_a_deduplicated_snapshot():
    palette = group_colors()

    assert len(palette) == 10
    assert len(set(palette)) == len(palette)
    assert palette == list(GROUP_COLORS)


def test_names_fit_the_column():
    """Имя цвета едет в ``research_group.color``: длиннее колонки его молча обрежет CRUD."""
    assert all(name == name.lower() for name in GROUP_COLORS)
    assert all(name.isalpha() for name in GROUP_COLORS)
    assert max(len(name) for name in GROUP_COLORS) <= GROUP_COLOR_MAX


def test_front_registry_covers_exactly_the_palette():
    """Половинки контракта не должны разъезжаться: имя без ступеней на фронте не покрасится.

    Тест читает TS-реестр как текст: это единственный шов между двумя языками, и молчаливое
    расхождение здесь выглядит как «цвет почему-то стал синим».
    """
    registry = _FRONT_REGISTRY.read_text(encoding="utf-8")
    mapped = re.findall(
        r"^  (\w+): +\{ light: '(#[0-9A-F]{6})', mid: '(#[0-9A-F]{6})', deep: '(#[0-9A-F]{6})' \},$",
        registry,
        re.M,
    )

    assert [name for name, *_ in mapped] == list(GROUP_COLORS)
    assert len({tuple(steps) for _, *steps in mapped}) == len(mapped)


def test_palette_is_immutable_and_copied_out():
    """``group_colors()`` отдаёт копию — правка ответа не портит константу."""
    assert isinstance(GROUP_COLORS, tuple)

    palette = group_colors()
    palette.append("junk")

    assert "junk" not in group_colors()
