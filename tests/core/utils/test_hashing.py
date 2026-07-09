from __future__ import annotations

import pytest

from src.core.utils.hashing import dict_hash, text_hash


@pytest.mark.pure
def test_text_hash_length_is_22():
    assert len(text_hash("hello")) == 22


@pytest.mark.pure
def test_text_hash_none_equals_empty_string():
    assert text_hash(None) == text_hash("")


@pytest.mark.pure
def test_text_hash_deterministic():
    assert text_hash("same body") == text_hash("same body")


@pytest.mark.pure
def test_text_hash_differs_on_content_change():
    assert text_hash("a") != text_hash("b")


@pytest.mark.pure
def test_text_hash_sensitive_to_whitespace():
    # канонизация делается выше по pipeline (на стороне вызывающего кода),
    # сам хеш — чистая функция от полученной строки
    assert text_hash("hello") != text_hash("hello ")


@pytest.mark.pure
def test_text_hash_is_lowercase_hex():
    # SHA-256 hexdigest[:22]: алфавит строго [0-9a-f], без '_'/'-'/'='
    digest = text_hash("hello")
    assert all(c in "0123456789abcdef" for c in digest)


@pytest.mark.pure
def test_dict_hash_length_is_22():
    assert len(dict_hash({"a": "1"})) == 22


@pytest.mark.pure
def test_dict_hash_is_lowercase_hex():
    assert all(c in "0123456789abcdef" for c in dict_hash({"a": "1"}))


@pytest.mark.pure
def test_dict_hash_independent_of_insertion_order():
    assert dict_hash({"a": "1", "b": "2"}) == dict_hash({"b": "2", "a": "1"})
