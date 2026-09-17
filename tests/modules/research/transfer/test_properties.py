"""Свойства переноса на сгенерированных входах (hypothesis).

Примеры в соседних файлах проверяют случаи, которые я придумал; здесь проверяются утверждения,
которые обязаны держаться на **любом** входе. Три из четырёх свойств — модельные: результат
сверяется с независимой реализацией того же правила, а не с самим собой (модельные свойства —
самый результативный класс по мутационным замерам, инвариант «ничего не упало» — самый слабый).

Независимость модели здесь не формальность: подмена ссылок сверяется с **своим** сканером,
написанным вручную по границам слова, а не с той же регуляркой, что и в коде, — иначе тест
доказывал бы лишь то, что регулярка равна самой себе.
"""

from __future__ import annotations

import asyncio
import string
from datetime import datetime

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.modules.research.constants import CODE_LEN
from src.modules.research.transfer.naming import MAX_STEM_LENGTH, archive_file_name
from src.modules.research.transfer.refs import (
    WEB_SEARCH_CODE_LEN,
    collect_references,
    rewrite_references,
)
from src.modules.research.transfer.remap import assign_substitutes, substitute_code

pytestmark = pytest.mark.pure

_RESEARCH_PREFIXES = ("RESEARCH", "AREA", "NOTE", "QUERY", "SOURCE", "GROUP")
_WEB_SEARCH_PREFIXES = ("SEARCH", "PAGE")
_HEX = "0123456789abcdef"

codes = st.text(alphabet=_HEX, min_size=CODE_LEN, max_size=CODE_LEN)
wide_codes = st.text(alphabet=_HEX, min_size=WEB_SEARCH_CODE_LEN, max_size=WEB_SEARCH_CODE_LEN)
prose = st.text(
    alphabet=st.sampled_from(list(string.ascii_letters + " \n.,`«»-0123456789абвгде")),
    max_size=40,
)


def _references(prefixes: tuple[str, ...], code_strategy) -> st.SearchStrategy[tuple[str, str]]:
    return st.tuples(st.sampled_from(prefixes), code_strategy)


any_reference = st.one_of(
    _references(_RESEARCH_PREFIXES, codes), _references(_WEB_SEARCH_PREFIXES, wide_codes)
)


@st.composite
def body_with_references(draw) -> tuple[str, list[tuple[str, str]]]:
    """Текст, в который вкраплены ссылки; возвращает и сам текст, и список вкраплённых пар."""
    references = draw(st.lists(any_reference, max_size=6))
    parts: list[str] = [draw(prose)]
    for prefix, code in references:
        parts.append(f"{prefix}@{code}")
        parts.append(draw(prose))
    return " ".join(parts), references


def _model_rewrite(text: str, mapping: dict[tuple[str, str], str]) -> tuple[str, int]:
    """Независимая модель подмены: посимвольный сканер вместо регулярки.

    Ссылка — это тип-слово на границе слова, ``@`` и ровно ``length`` hex-символов, за которыми
    не идёт ещё один hex. Каждое вхождение переписывается **один раз**: сканер двигается дальше
    по исходному тексту, поэтому подставленное значение повторно не рассматривается.
    """
    lengths = {prefix: CODE_LEN for prefix in _RESEARCH_PREFIXES}
    lengths.update({prefix: WEB_SEARCH_CODE_LEN for prefix in _WEB_SEARCH_PREFIXES})

    result: list[str] = []
    rewritten = 0
    position = 0
    while position < len(text):
        match = None
        for prefix, length in lengths.items():
            if not text.startswith(f"{prefix}@", position):
                continue
            if position > 0 and (text[position - 1].isalnum() or text[position - 1] == "_"):
                continue
            head = position + len(prefix) + 1
            code = text[head : head + length]
            if len(code) < length or any(character not in _HEX for character in code):
                continue
            if head + length < len(text) and text[head + length] in _HEX:
                continue
            match = (prefix, code, head + length)
            break

        if match is None:
            result.append(text[position])
            position += 1
            continue

        prefix, code, end = match
        replacement = mapping.get((prefix, code), code)
        if replacement != code:
            rewritten += 1
        result.append(f"{prefix}@{replacement}")
        position = end

    return "".join(result), rewritten


@given(body_with_references(), st.data())
def test_rewriting_matches_an_independent_scanner(body_and_references, data):
    """Модельное свойство: результат совпадает со сканером, написанным независимо."""
    text, references = body_and_references
    mapping = {}
    for prefix, code in references:
        if data.draw(st.booleans()):
            length = CODE_LEN if prefix in _RESEARCH_PREFIXES else WEB_SEARCH_CODE_LEN
            mapping[(prefix, code)] = data.draw(
                st.text(alphabet=_HEX, min_size=length, max_size=length)
            )

    assert rewrite_references(text, mapping) == _model_rewrite(text, mapping)


@given(body_with_references())
def test_a_chain_of_substitutions_never_forms(body_and_references):
    """Метаморфное свойство: `a→b` и `b→c` в одной карте не складываются в `a→c`.

    Это главный отказ, ради которого подмена сделана одним проходом: последовательная замена
    увела бы ссылку через промежуточное значение, и заметить это в теле было бы нечем.
    """
    text, references = body_and_references
    assume(references)
    prefix, first = references[0]
    length = len(first)
    second = ("1" * length)[:length]
    third = ("2" * length)[:length]
    assume(first not in (second, third))

    rewritten, _ = rewrite_references(text, {(prefix, first): second, (prefix, second): third})

    assert f"{prefix}@{third}" not in rewritten
    assert f"{prefix}@{second}" in rewritten


@given(body_with_references())
def test_an_identity_map_changes_nothing(body_and_references):
    text, references = body_and_references
    identity = {(prefix, code): code for prefix, code in references}

    assert rewrite_references(text, identity) == (text, 0)


@given(body_with_references())
def test_every_reference_the_body_carries_is_collected(body_and_references):
    text, references = body_and_references

    assert collect_references(text) >= {
        pair for pair in references if f"{pair[0]}@{pair[1]}" in text
    }


@given(
    st.text(min_size=1, max_size=40),
    st.text(alphabet=_HEX, min_size=CODE_LEN, max_size=CODE_LEN),
)
def test_a_file_name_is_always_safe_to_write(title, code):
    """Инвариант имени: что бы ни было в названии, файл можно создать на любой системе."""
    name = archive_file_name(title, code)

    stem = name[: -len(".urch")]
    assert name.endswith(".urch")
    assert stem, "пустое имя неотличимо от другого такого же"
    assert not (set(stem) & set('/\\:*?"<>|'))
    assert not any(ord(character) < 32 for character in stem)
    assert stem[-1] not in ". "
    assert len(stem) <= max(MAX_STEM_LENGTH, len(f"research-{code}"))


@given(
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=30),
    st.lists(codes, max_size=8, unique=True),
    st.sets(codes, max_size=8),
    st.sets(codes, max_size=8),
)
@settings(max_examples=50, deadline=None)
def test_substitutes_are_free_unique_and_reproducible(archive_id, origins, occupied, reserved):
    """Модельное свойство карты подмен: свободны, различны и воспроизводимы.

    Занятость базы моделируется множеством: именно этот контракт (``codes_in_use``) и есть то,
    что в бою отвечает база.
    """

    async def assign(taken: set[str]) -> dict[str, str]:
        async def codes_in_use(candidates: list[str]) -> set[str]:
            return {candidate for candidate in candidates if candidate in taken}

        return await assign_substitutes(
            archive_id=archive_id,
            origins=list(origins),
            codes_in_use=codes_in_use,
            reserved=set(reserved),
        )

    assigned = asyncio.run(assign(set(occupied)))
    again = asyncio.run(assign(set(occupied)))

    assert assigned == again, "повторный заход обязан построить ту же карту"
    assert set(assigned) == set(origins)
    assert not set(assigned.values()) & set(occupied)
    assert not set(assigned.values()) & set(reserved)
    assert len(set(assigned.values())) == len(assigned)
    assert all(len(code) == CODE_LEN for code in assigned.values())
    assert all(set(code) <= set(_HEX) for code in assigned.values())


@given(st.text(min_size=1, max_size=20), codes, st.integers(min_value=0, max_value=5))
def test_a_substitute_keeps_the_shape_of_the_code_it_replaces(archive_id, code, attempt):
    substitute = substitute_code(archive_id, code, attempt)

    assert len(substitute) == len(code)
    assert set(substitute) <= set(_HEX)
    assert substitute == substitute_code(archive_id, code, attempt)


@given(st.text(min_size=1, max_size=20), codes, codes)
def test_two_archives_do_not_share_a_substitute(first_archive, second_archive, code):
    assume(first_archive != second_archive)

    assert substitute_code(first_archive, code, 0) != substitute_code(second_archive, code, 0)


@given(
    st.datetimes(
        min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1)
    ).map(lambda moment: moment.replace(microsecond=0))
)
def test_a_moment_survives_the_archive_unchanged(moment):
    """Круг «в архив и обратно» для времени: формат без долей секунды не теряет самой секунды."""
    from src.core.utils.date import datetime_from_agent, datetime_to_agent

    assert datetime_from_agent(datetime_to_agent(moment)) == moment
