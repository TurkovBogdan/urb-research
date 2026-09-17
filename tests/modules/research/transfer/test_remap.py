"""Перевыпуск кода при столкновении с местной базой.

Подмена обязана быть выводимой, а не случайной: прерванный импорт, продолженный со второй
попытки, должен построить ту же карту и дописать записи, а не создать их второй комплект.
Отсюда все проверки ниже — детерминизм, форма кода и обход занятых значений.
"""

from __future__ import annotations

import pytest

from src.modules.research.constants import CODE_LEN
from src.modules.research.transfer.refs import WEB_SEARCH_CODE_LEN
from src.modules.research.transfer.remap import CodesInUse, assign_substitutes, substitute_code

pytestmark = pytest.mark.pure

ARCHIVE = "01JB0000000000000000000000"
OTHER_ARCHIVE = "01JB9999999999999999999999"
HEX_ALPHABET = set("0123456789abcdef")


def _database_holding(*codes: str) -> CodesInUse:
    """База, в которой заняты ровно перечисленные коды."""

    async def codes_in_use(candidates: list[str]) -> set[str]:
        return {candidate for candidate in candidates if candidate in set(codes)}

    return codes_in_use


def test_the_same_input_always_yields_the_same_substitute():
    assert substitute_code(ARCHIVE, "a" * CODE_LEN, 0) == substitute_code(ARCHIVE, "a" * CODE_LEN, 0)


@pytest.mark.parametrize("length", [CODE_LEN, WEB_SEARCH_CODE_LEN], ids=["research", "web-search"])
def test_a_substitute_keeps_the_length_and_the_alphabet_of_the_original(length):
    """Код той же длины и того же алфавита — иначе подмена не влезет в колонку и в регулярку ссылок."""
    substitute = substitute_code(ARCHIVE, "a" * length, 0)
    assert len(substitute) == length
    assert set(substitute) <= HEX_ALPHABET


def test_two_archives_of_the_same_record_get_different_substitutes():
    """Соль — идентификатор выгрузки: две копии одного исследования ложатся в базу рядом."""
    origin = "a" * CODE_LEN
    assert substitute_code(ARCHIVE, origin, 0) != substitute_code(OTHER_ARCHIVE, origin, 0)


def test_the_next_attempt_yields_another_substitute():
    origin = "a" * CODE_LEN
    assert substitute_code(ARCHIVE, origin, 0) != substitute_code(ARCHIVE, origin, 1)


def test_two_origins_never_share_a_substitute():
    assert substitute_code(ARCHIVE, "a" * CODE_LEN, 0) != substitute_code(ARCHIVE, "b" * CODE_LEN, 0)


async def test_a_substitute_taken_in_the_database_is_stepped_over():
    origin = "a" * CODE_LEN
    assigned = await assign_substitutes(
        archive_id=ARCHIVE,
        origins=[origin],
        codes_in_use=_database_holding(substitute_code(ARCHIVE, origin, 0)),
        reserved=set(),
    )
    assert assigned == {origin: substitute_code(ARCHIVE, origin, 1)}


async def test_attempts_keep_stepping_until_a_free_value_turns_up():
    origin = "a" * CODE_LEN
    occupied = [substitute_code(ARCHIVE, origin, attempt) for attempt in (0, 1, 2)]
    assigned = await assign_substitutes(
        archive_id=ARCHIVE,
        origins=[origin],
        codes_in_use=_database_holding(*occupied),
        reserved=set(),
    )
    assert assigned == {origin: substitute_code(ARCHIVE, origin, 3)}


async def test_a_substitute_already_handed_out_in_this_run_is_stepped_over():
    """Без второй проверки два кода архива схлопнулись бы в одну запись базы."""
    origin = "a" * CODE_LEN
    assigned = await assign_substitutes(
        archive_id=ARCHIVE,
        origins=[origin],
        codes_in_use=_database_holding(),
        reserved={substitute_code(ARCHIVE, origin, 0)},
    )
    assert assigned == {origin: substitute_code(ARCHIVE, origin, 1)}


async def test_an_assigned_substitute_joins_the_reserved_set():
    """Реестр розданного общий на прогон: следующая таблица обязана видеть выданные коды."""
    origin = "a" * CODE_LEN
    reserved: set[str] = set()
    assigned = await assign_substitutes(
        archive_id=ARCHIVE, origins=[origin], codes_in_use=_database_holding(), reserved=reserved
    )
    assert reserved == set(assigned.values())


async def test_every_origin_gets_its_own_substitute():
    origins = ["a" * CODE_LEN, "b" * CODE_LEN, "c" * CODE_LEN]
    assigned = await assign_substitutes(
        archive_id=ARCHIVE, origins=origins, codes_in_use=_database_holding(), reserved=set()
    )
    assert set(assigned) == set(origins)
    assert len(set(assigned.values())) == len(origins)


async def test_repeating_the_call_rebuilds_the_same_map():
    """Тот же архив в той же базе — та же карта; между заходами не хранится ничего."""
    origins = ["a" * CODE_LEN, "b" * CODE_LEN]
    database = _database_holding(substitute_code(ARCHIVE, origins[0], 0))
    first = await assign_substitutes(
        archive_id=ARCHIVE, origins=origins, codes_in_use=database, reserved=set()
    )
    second = await assign_substitutes(
        archive_id=ARCHIVE, origins=origins, codes_in_use=database, reserved=set()
    )
    assert first == second


async def test_no_origins_yield_an_empty_map():
    assert (
        await assign_substitutes(
            archive_id=ARCHIVE, origins=[], codes_in_use=_database_holding(), reserved=set()
        )
        == {}
    )
