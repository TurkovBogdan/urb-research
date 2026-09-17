"""Строка таблицы ↔ объект JSON: единственное правило перевода на все таблицы архива.

Модель здесь своя, игрушечная: проверяется само правило (даты, умолчания, ширина колонок), а
не состав конкретной таблицы research — тот меняется миграциями, и тест ходил бы за ним следом,
ничего при этом не утверждая.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

from src.core.utils.date import utc_now
from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.rows import (
    clip_to_columns,
    json_to_values,
    row_to_json,
    same_moment,
)

pytestmark = pytest.mark.pure

_Base = declarative_base()


class _Probe(_Base):
    """Колонки подобраны по ветвям перевода: обязательная без умолчания, с умолчанием,
    с вычисляемым умолчанием, обнуляемая, дата, JSON и текст без ограничения длины."""

    __tablename__ = "transfer_probe"

    code = Column(String(10), primary_key=True)
    title = Column(String(8), nullable=False)
    note = Column(String(4), nullable=True)
    status = Column(String(6), nullable=False, default="draft")
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=True)
    body = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)


MOMENT = datetime(2026, 1, 2, 3, 4, 5)
MOMENT_TEXT = "2026-01-02 03:04:05"


def _row(**overrides) -> _Probe:
    values = {
        "code": "0123456789",
        "title": "название",
        "note": None,
        "status": "draft",
        "attempts": 0,
        "created_at": MOMENT,
        "updated_at": None,
        "body": "тело",
        "payload": {"k": "v"},
    }
    return _Probe(**{**values, **overrides})


def test_a_date_leaves_in_sql_format_without_the_t_separator():
    """Тот же формат, каким даты уходят в API: ISO с «T» фронт и агент читают как чужое время."""
    assert row_to_json(_row())["created_at"] == MOMENT_TEXT
    assert "T" not in row_to_json(_row())["created_at"]


def test_an_aware_date_leaves_as_naive_utc():
    aware = datetime(2026, 1, 2, 6, 4, 5, tzinfo=timezone(timedelta(hours=3)))
    assert row_to_json(_row(created_at=aware))["created_at"] == MOMENT_TEXT


def test_a_json_column_stays_an_object():
    assert row_to_json(_row())["payload"] == {"k": "v"}


def test_the_omitted_columns_do_not_reach_the_archive():
    """Тело уезжает отдельной записью архива, а не полем строки — иначе оно легло бы дважды."""
    values = row_to_json(_row(), omit=("body",))
    assert "body" not in values
    assert set(values) == {column.name for column in _Probe.__table__.columns} - {"body"}


def test_an_unknown_key_is_ignored():
    """Архив мог приехать с версии, где колонок больше: лишнее поле — не повод отказывать."""
    values = json_to_values(_Probe, {**row_to_json(_row()), "future_column": "?"})
    assert "future_column" not in values


def test_a_date_comes_back_as_a_datetime():
    assert json_to_values(_Probe, row_to_json(_row()))["created_at"] == MOMENT


def test_a_missing_nullable_column_comes_back_empty():
    archived = row_to_json(_row())
    del archived["note"]
    assert json_to_values(_Probe, archived)["note"] is None


def test_a_missing_column_is_filled_from_its_default():
    archived = row_to_json(_row())
    del archived["status"]
    assert json_to_values(_Probe, archived)["status"] == "draft"


def test_a_falsy_default_counts_as_a_default():
    """Ноль и пустая строка — законные умолчания; принять их за «умолчания нет» значит отказать
    в импорте строке, которой ничего не мешает лечь в базу."""
    archived = row_to_json(_row())
    del archived["attempts"]
    assert json_to_values(_Probe, archived)["attempts"] == 0


@pytest.mark.parametrize("column", ["code", "title"], ids=["key", "required"])
def test_a_required_column_without_a_default_is_refused(column):
    archived = row_to_json(_row())
    del archived[column]
    with pytest.raises(ArchiveError, match=column):
        json_to_values(_Probe, archived)


def test_a_required_column_whose_default_is_computed_is_refused():
    """Вычислить `created_at` на месте значило бы выдать время импорта за время создания записи."""
    archived = row_to_json(_row())
    del archived["created_at"]
    with pytest.raises(ArchiveError, match="created_at"):
        json_to_values(_Probe, archived)


def test_an_omitted_column_is_neither_parsed_nor_filled():
    """Суррогатный ключ выдаёт принимающая база: его отсутствие в строке — норма, а не отказ."""
    archived = row_to_json(_row())
    del archived["title"]
    assert "title" not in json_to_values(_Probe, archived, omit=("title",))


@pytest.mark.parametrize(
    "value", ["2026-01-02T03:04:05", "2026-01-02", "позавчера", 1767322625],
    ids=["iso-t", "date-only", "words", "epoch"],
)
def test_a_value_that_is_not_a_date_is_refused_by_field_name(value):
    """Имя поля в отказе — единственное, за что можно зацепиться, разбирая чужой архив."""
    with pytest.raises(ArchiveError, match="created_at"):
        json_to_values(_Probe, {**row_to_json(_row()), "created_at": value})


def test_an_empty_date_stays_empty():
    assert json_to_values(_Probe, {**row_to_json(_row()), "updated_at": None})["updated_at"] is None


def test_the_same_second_with_and_without_microseconds_is_the_same_moment():
    """SQLite хранит микросекунды, архив — секунды: на точном сравнении своя же запись после
    круга «экспорт → импорт» перестала бы опознаваться и легла бы дублем."""
    assert same_moment(MOMENT.replace(microsecond=765432), MOMENT)


def test_different_seconds_are_different_moments():
    assert not same_moment(MOMENT + timedelta(seconds=1), MOMENT)


@pytest.mark.parametrize(
    ("local", "archived", "expected"),
    [(None, None, True), (MOMENT, None, False), (None, MOMENT, False)],
    ids=["both-empty", "local-only", "archived-only"],
)
def test_an_empty_moment_equals_only_another_empty_moment(local, archived, expected):
    assert same_moment(local, archived) is expected


def test_a_value_wider_than_its_column_is_clipped_and_named():
    """Политика та же, что у обычной правки через MCP: длинное название режется, а не роняет запись."""
    values, clipped = clip_to_columns(_Probe, {"title": "x" * 20, "code": "0123456789"})
    assert values["title"] == "x" * 8
    assert clipped == ["title"]


def test_every_clipped_field_is_named():
    values, clipped = clip_to_columns(_Probe, {"title": "x" * 20, "note": "y" * 20})
    assert (values["title"], values["note"]) == ("x" * 8, "y" * 4)
    assert sorted(clipped) == ["note", "title"]


def test_a_value_within_its_column_is_left_alone():
    values, clipped = clip_to_columns(_Probe, {"title": "x" * 8})
    assert values["title"] == "x" * 8
    assert clipped == []


def test_a_column_without_a_width_is_never_clipped():
    """`Text` ширины не имеет: тело исследования подрезать не по чему и не за чем."""
    _, clipped = clip_to_columns(_Probe, {"body": "x" * 10_000})
    assert clipped == []


@pytest.mark.parametrize("value", [None, 12345, {"k": "v" * 50}], ids=["none", "int", "json"])
def test_a_value_that_is_not_text_is_never_clipped(value):
    _, clipped = clip_to_columns(_Probe, {"payload": value, "attempts": value})
    assert clipped == []
