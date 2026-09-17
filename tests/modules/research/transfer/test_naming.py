"""Имя файла архива: что остаётся от названия исследования после обеззараживания.

Файл ложится на чужую файловую систему, поэтому проверяется ровно то, чем Windows и POSIX
расходятся с текстом, который писал человек: разделители пути, запрещённые символы,
управляющие, хвостовая точка и длина. Длина меряется в code points — байтовый предел резал бы
русское название вдвое короче английского при одинаковой «на глаз» ширине.
"""

from __future__ import annotations

import pytest

from src.modules.research.transfer.constants import ARCHIVE_EXTENSION
from src.modules.research.transfer.naming import MAX_STEM_LENGTH, archive_file_name

pytestmark = pytest.mark.pure

CODE = "0123456789"


@pytest.mark.parametrize(
    "title",
    ['a/b', 'a\\b', 'a:b', 'a"b', 'a<b', 'a>b', 'a|b', 'a?b', 'a*b', 'a\x00b', 'a\tb', 'a\nb'],
    ids=[
        "slash", "backslash", "colon", "quote", "less", "greater",
        "pipe", "question", "star", "nul", "tab", "newline",
    ],
)
def test_a_character_forbidden_in_a_file_name_becomes_a_dash(title):
    assert archive_file_name(title, CODE) == f"a-b{ARCHIVE_EXTENSION}"


def test_a_run_of_forbidden_characters_collapses_into_one_dash():
    """Иначе «Отчёт :: 2026» дал бы имя с частоколом дефисов на месте одного разделителя."""
    assert archive_file_name("a///b", CODE) == f"a-b{ARCHIVE_EXTENSION}"


def test_a_run_of_spaces_collapses_into_one_space():
    assert archive_file_name("a   b", CODE) == f"a b{ARCHIVE_EXTENSION}"


def test_the_name_never_becomes_a_path():
    """Имя уходит в заголовок скачивания: уцелевший разделитель пути увёл бы файл в каталог."""
    name = archive_file_name("отчёт/2026\\итог", CODE)
    assert "/" not in name and "\\" not in name


@pytest.mark.parametrize(
    ("title", "expected_stem"),
    [("report.", "report"), ("report ", "report"), ("report . . ", "report")],
    ids=["dot", "space", "mix"],
)
def test_trailing_dots_and_spaces_are_cut_off(title, expected_stem):
    """Windows не открывает файл, имя которого кончается точкой или пробелом."""
    assert archive_file_name(title, CODE) == f"{expected_stem}{ARCHIVE_EXTENSION}"


def test_the_tail_is_trimmed_after_the_cut_and_not_before():
    """Срез по длине сам способен оставить точку последней — значит чистить хвост надо после него."""
    title = "x" * (MAX_STEM_LENGTH - 2) + " ..."
    assert archive_file_name(title, CODE) == f"{'x' * (MAX_STEM_LENGTH - 2)}{ARCHIVE_EXTENSION}"


@pytest.mark.parametrize("letter", ["x", "я"], ids=["latin", "cyrillic"])
def test_a_long_title_is_cut_to_the_same_number_of_code_points_in_any_alphabet(letter):
    """Кириллица весит в UTF-8 вдвое: срез по байтам дал бы русскому названию 40 знаков вместо 80."""
    stem = archive_file_name(letter * 200, CODE).removesuffix(ARCHIVE_EXTENSION)
    assert len(stem) == MAX_STEM_LENGTH


def test_a_title_shorter_than_the_limit_is_kept_whole():
    assert archive_file_name("Короткое название", CODE) == f"Короткое название{ARCHIVE_EXTENSION}"


@pytest.mark.parametrize("title", ["", "   ", "...", " . "], ids=["empty", "spaces", "dots", "mix"])
def test_a_title_that_leaves_nothing_falls_back_to_the_code(title):
    assert archive_file_name(title, CODE) == f"research-{CODE}{ARCHIVE_EXTENSION}"


@pytest.mark.parametrize("title", ["///", "?", "<<>>"], ids=["slashes", "question", "brackets"])
def test_a_title_eaten_whole_by_sanitising_falls_back_to_the_code(title):
    assert archive_file_name(title, CODE) == f"research-{CODE}{ARCHIVE_EXTENSION}"


@pytest.mark.parametrize(
    "title", ["", "обычное название", "a/b", "x" * 300, "🙂"],
    ids=["empty", "plain", "unsafe", "long", "emoji"],
)
def test_the_extension_is_always_urch(title):
    assert archive_file_name(title, CODE).endswith(ARCHIVE_EXTENSION)
