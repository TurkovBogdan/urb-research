"""Schema validation + build_store."""

from __future__ import annotations

import dataclasses

import pytest

from src.core.settings.fields import IntField, MultiChoiceField, StrField
from src.core.settings.schema import validate_schema
from src.core.settings.store import build_store


@pytest.mark.pure
def test_validate_schema_duplicate_keys_rejected():
    schema = (
        IntField(key="x", label="X", default_=1),
        IntField(key="x", label="X again", default_=2),
    )
    with pytest.raises(ValueError):
        validate_schema("m", schema)


@pytest.mark.pure
def test_validate_schema_default_must_pass_constraints():
    schema = (IntField(key="x", label="X", default_=200, max=100),)
    with pytest.raises(ValueError):
        validate_schema("m", schema)


@pytest.mark.pure
def test_validate_schema_key_format():
    bad = (IntField(key="BadKey", label="X", default_=1),)
    with pytest.raises(ValueError):
        validate_schema("m", bad)


@pytest.mark.pure
def test_build_store_uses_defaults_for_missing_keys():
    schema = (
        IntField(key="n", label="N", default_=42),
        StrField(key="s", label="S", default_="hi"),
    )
    store = build_store("m", schema, {"n": 7})
    assert store.n == 7
    assert store.s == "hi"


@pytest.mark.pure
def test_build_store_returns_frozen_dataclass():
    schema = (IntField(key="n", label="N", default_=1),)
    store = build_store("m", schema, {"n": 1})
    assert dataclasses.is_dataclass(store)
    with pytest.raises(dataclasses.FrozenInstanceError):
        store.n = 99


@pytest.mark.pure
def test_build_store_freezes_multichoice_to_tuple():
    schema = (
        MultiChoiceField(
            key="r", label="R", default_=("a",),
            options={"a": "A", "b": "B"},
        ),
    )
    store = build_store("m", schema, {"r": ["a", "b"]})
    assert store.r == ("a", "b")
    assert isinstance(store.r, tuple)
