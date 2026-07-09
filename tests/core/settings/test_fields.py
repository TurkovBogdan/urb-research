"""Field-классы: parse/serialize/validate/ui_descriptor."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.core.settings.fields import (
    BoolField,
    ChoiceField,
    DateField,
    DateTimeField,
    FloatField,
    IntField,
    ListField,
    MultiChoiceField,
    StrField,
)


# ── Int ──────────────────────────────────────────────────────────────────


@pytest.mark.pure
def test_int_roundtrip():
    f = IntField(key="x", label="X", default_=3, min=0, max=10)
    assert f.parse(f.serialize(7)) == 7
    f.validate(0)
    f.validate(10)
    with pytest.raises(ValueError):
        f.validate(-1)
    with pytest.raises(ValueError):
        f.validate(11)
    with pytest.raises(ValueError):
        f.validate("3")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        f.validate(True)  # bool — не int в нашем мире


# ── Float ────────────────────────────────────────────────────────────────


@pytest.mark.pure
def test_float_roundtrip():
    f = FloatField(key="x", label="X", default_=1.5, min=0.0, max=10.0,
                   step=0.1, decimals=2)
    assert f.parse(f.serialize(3.14)) == pytest.approx(3.14)
    f.validate(0.0)
    f.validate(10.0)
    with pytest.raises(ValueError):
        f.validate(-0.1)
    desc = f.ui_descriptor()
    assert desc["step"] == 0.1
    assert desc["decimals"] == 2


# ── Bool ─────────────────────────────────────────────────────────────────


@pytest.mark.pure
def test_bool_roundtrip_and_validation():
    f = BoolField(key="x", label="X", default_=True)
    assert f.default() is True
    assert f.parse(f.serialize(True)) is True
    assert f.parse(f.serialize(False)) is False
    assert f.parse("true") is True
    assert f.parse("false") is False
    f.validate(True)
    f.validate(False)
    with pytest.raises(ValueError):
        f.validate("true")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        f.validate(1)  # type: ignore[arg-type]
    assert f.ui_descriptor()["kind"] == "bool"


# ── Str ──────────────────────────────────────────────────────────────────


@pytest.mark.pure
def test_str_lines_descriptor():
    f1 = StrField(key="a", label="A", lines=1)
    f5 = StrField(key="a", label="A", lines=5)
    assert f1.ui_descriptor()["lines"] == 1
    assert f5.ui_descriptor()["lines"] == 5


@pytest.mark.pure
def test_str_length_and_pattern():
    f = StrField(key="a", label="A", min_length=1, max_length=4,
                 pattern=r"[a-z]+")
    f.validate("ab")
    with pytest.raises(ValueError):
        f.validate("")
    with pytest.raises(ValueError):
        f.validate("abcde")
    with pytest.raises(ValueError):
        f.validate("AB")


# ── Date / DateTime ──────────────────────────────────────────────────────


@pytest.mark.pure
def test_date_roundtrip():
    f = DateField(key="d", label="D")
    s = f.serialize(date(2026, 5, 12))
    assert s == "2026-05-12"
    assert f.parse(s) == date(2026, 5, 12)


@pytest.mark.pure
def test_datetime_tz_aware_normalized_to_naive_utc():
    f = DateTimeField(key="t", label="T")
    aware = datetime(2026, 5, 12, 15, 0, tzinfo=timezone.utc)
    parsed = f.parse(f.serialize(aware))
    assert parsed.tzinfo is None
    assert parsed == datetime(2026, 5, 12, 15, 0)


@pytest.mark.pure
def test_datetime_naive_passthrough():
    f = DateTimeField(key="t", label="T")
    naive = datetime(2026, 5, 12, 15, 0)
    assert f.parse(f.serialize(naive)) == naive


# ── Choice / MultiChoice ─────────────────────────────────────────────────


@pytest.mark.pure
def test_choice_validate_unknown_rejected():
    f = ChoiceField(
        key="m", label="M", default_="a", options={"a": "A", "b": "B"},
    )
    f.validate("a")
    with pytest.raises(ValueError):
        f.validate("z")


@pytest.mark.pure
def test_choice_ui_descriptor_options_order():
    f = ChoiceField(
        key="m", label="M", default_="x",
        options={"x": "X", "y": "Y", "z": "Z"},
    )
    codes = [o["code"] for o in f.ui_descriptor()["options"]]
    assert codes == ["x", "y", "z"]


@pytest.mark.pure
def test_multichoice_roundtrip_and_validation():
    f = MultiChoiceField(
        key="r", label="R", default_=("a",),
        options={"a": "A", "b": "B"}, min_items=1, max_items=2,
    )
    text = f.serialize(["a", "b"])
    assert f.parse(text) == ["a", "b"]
    f.validate(["a"])
    with pytest.raises(ValueError):
        f.validate([])  # min_items=1
    with pytest.raises(ValueError):
        f.validate(["a", "b", "extra"])  # not in options


# ── List ─────────────────────────────────────────────────────────────────


@pytest.mark.pure
def test_list_of_int_validates_each_item():
    f = ListField(
        key="xs", label="Xs",
        item=IntField(key="item", label="", min=0, max=100),
        default_=(),
    )
    text = f.serialize([1, 2, 3])
    assert f.parse(text) == [1, 2, 3]
    f.validate([0, 100])
    with pytest.raises(ValueError):
        f.validate([1, -1])
    with pytest.raises(ValueError):
        f.validate([1, 101])


@pytest.mark.pure
def test_list_default_is_fresh_list():
    f = ListField(
        key="xs", label="Xs",
        item=StrField(key="item", label=""),
        default_=("a", "b"),
    )
    d1 = f.default()
    d2 = f.default()
    assert d1 == d2
    d1.append("mutated")
    assert "mutated" not in f.default()


# ── repr_for_log ─────────────────────────────────────────────────────────


@pytest.mark.pure
def test_repr_for_log_default_is_repr():
    f = IntField(key="x", label="X", default_=1)
    assert f.repr_for_log(42) == "42"
