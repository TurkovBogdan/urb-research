"""Ссылки ``TYPE@hash`` в телах: сбор и подмена по карте импорта.

Главная проверка файла — отсутствие каскада: карта, где новый код одной записи совпал со
старым кодом другой, обязана переставить каждую ссылку ровно один раз. Пара-за-парой замена
сцепилась бы сама с собой и увела бы ссылку через промежуточный код в чужую запись — молча,
без единой ошибки в логе.
"""

from __future__ import annotations

import pytest

from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    CODE_LEN,
    NOTE_CODE_PREFIX,
    PAGE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
)
from src.modules.research.transfer.refs import (
    WEB_SEARCH_CODE_LEN,
    collect_references,
    rewrite_references,
)

pytestmark = pytest.mark.pure

A = "a" * CODE_LEN
B = "b" * CODE_LEN
C = "c" * CODE_LEN
LONG = "d" * WEB_SEARCH_CODE_LEN


def test_a_substitution_chain_never_forms():
    """`a→b` и `b→c` в одной карте: ссылка на `a` обязана встать на `b`, а не доехать до `c`."""
    text = f"см. {AREA_CODE_PREFIX}@{A} и {AREA_CODE_PREFIX}@{B}"
    rewritten, moved = rewrite_references(
        text, {(AREA_CODE_PREFIX, A): B, (AREA_CODE_PREFIX, B): C}
    )
    assert rewritten == f"см. {AREA_CODE_PREFIX}@{B} и {AREA_CODE_PREFIX}@{C}"
    assert moved == 2


def test_a_chain_does_not_form_even_when_the_pairs_are_ordered_against_it():
    """Порядок пар в карте не должен ничего значить — иначе поведение зависело бы от словаря."""
    rewritten, _ = rewrite_references(
        f"{AREA_CODE_PREFIX}@{A}", {(AREA_CODE_PREFIX, B): C, (AREA_CODE_PREFIX, A): B}
    )
    assert rewritten == f"{AREA_CODE_PREFIX}@{B}"


@pytest.mark.parametrize(
    "template",
    [
        "`{ref}`",
        "```\n{ref}\n```",
        "```python\n# {ref}\n```",
        "[текст]({ref})",
        "| {ref} |",
    ],
    ids=["inline-code", "fence", "fenced-python", "link", "table"],
)
def test_a_reference_moves_wherever_the_markup_puts_it(template):
    """Подмена работает с текстом, а не с разметкой: код в блоке кода — та же ссылка на запись."""
    rewritten, moved = rewrite_references(
        template.format(ref=f"{AREA_CODE_PREFIX}@{A}"), {(AREA_CODE_PREFIX, A): B}
    )
    assert rewritten == template.format(ref=f"{AREA_CODE_PREFIX}@{B}")
    assert moved == 1


def test_a_longer_hash_is_not_bitten_off_by_the_short_pattern():
    """22-значный код web_search стоит в телах рядом; срез его первых десяти знаков увёл бы
    ссылку в никуда, а сам код перестал бы существовать."""
    text = f"{SOURCE_DOCUMENT_CODE_PREFIX}@{LONG}"
    rewritten, moved = rewrite_references(text, {(SOURCE_DOCUMENT_CODE_PREFIX, LONG[:CODE_LEN]): B})
    assert rewritten == text
    assert moved == 0


def test_a_longer_hash_is_not_collected_as_a_short_code():
    assert collect_references(f"{SOURCE_DOCUMENT_CODE_PREFIX}@{LONG}") == set()


@pytest.mark.parametrize(
    "prefix", [SEARCH_CODE_PREFIX, PAGE_CODE_PREFIX], ids=["search", "page"]
)
def test_a_web_search_reference_moves_by_its_own_length(prefix):
    moved_to = "e" * WEB_SEARCH_CODE_LEN
    rewritten, moved = rewrite_references(f"{prefix}@{LONG}", {(prefix, LONG): moved_to})
    assert rewritten == f"{prefix}@{moved_to}"
    assert moved == 1


def test_the_map_is_keyed_by_type_and_code_together():
    """Один и тот же хеш вправе оказаться кодом области в архиве и кодом заметки в базе."""
    rewritten, moved = rewrite_references(
        f"{AREA_CODE_PREFIX}@{A} {NOTE_CODE_PREFIX}@{A}",
        {(AREA_CODE_PREFIX, A): B, (NOTE_CODE_PREFIX, A): C},
    )
    assert rewritten == f"{AREA_CODE_PREFIX}@{B} {NOTE_CODE_PREFIX}@{C}"
    assert moved == 2


def test_a_reference_missing_from_the_map_is_left_alone():
    """Это либо запись, чей код не менялся, либо ссылка наружу архива — обе остаются как есть."""
    text = f"{AREA_CODE_PREFIX}@{A} {NOTE_CODE_PREFIX}@{C}"
    rewritten, moved = rewrite_references(text, {(AREA_CODE_PREFIX, A): A})
    assert rewritten == text
    assert moved == 0


def test_the_counter_counts_moves_and_not_matches():
    """Запись, чей код уцелел, стоит в карте сама на себя — переездом это не является."""
    _, moved = rewrite_references(
        f"{AREA_CODE_PREFIX}@{A} {AREA_CODE_PREFIX}@{A} {NOTE_CODE_PREFIX}@{A}",
        {(AREA_CODE_PREFIX, A): B, (NOTE_CODE_PREFIX, A): A},
    )
    assert moved == 2


@pytest.mark.parametrize("text", [None, ""], ids=["none", "empty"])
def test_an_absent_text_is_returned_as_is(text):
    assert rewrite_references(text, {(AREA_CODE_PREFIX, A): B}) == (text, 0)
    assert collect_references(text) == set()


def test_collect_finds_both_code_families():
    found = collect_references(
        f"{RESEARCH_CODE_PREFIX}@{A} {AREA_CODE_PREFIX}@{B} {SEARCH_CODE_PREFIX}@{LONG}"
    )
    assert found == {
        (RESEARCH_CODE_PREFIX, A),
        (AREA_CODE_PREFIX, B),
        (SEARCH_CODE_PREFIX, LONG),
    }


def test_a_reference_glued_to_a_word_is_not_a_reference():
    """Слово перед типом означает чужой текст, а не ссылку: `xAREA@…` подменять нельзя."""
    text = f"x{AREA_CODE_PREFIX}@{A}"
    assert collect_references(text) == set()
    assert rewrite_references(text, {(AREA_CODE_PREFIX, A): B}) == (text, 0)


def test_the_word_search_inside_research_is_not_a_separate_reference():
    """`RESEARCH@…` содержит `SEARCH@…` как подстроку — второй тип не должен её увидеть."""
    assert collect_references(f"{RESEARCH_CODE_PREFIX}@{A}") == {(RESEARCH_CODE_PREFIX, A)}


@pytest.mark.parametrize(
    "code", ["a" * (CODE_LEN - 1), "a" * (CODE_LEN + 1), "A" * CODE_LEN, "z" * CODE_LEN],
    ids=["short", "long", "uppercase", "not-hex"],
)
def test_a_code_of_the_wrong_shape_is_not_a_reference(code):
    assert collect_references(f"{AREA_CODE_PREFIX}@{code}") == set()


def test_an_unknown_type_word_is_not_a_reference():
    assert collect_references(f"FOO@{A}") == set()
