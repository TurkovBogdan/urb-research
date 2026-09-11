"""core_connectors: шифрование значений — конверт, формат, связывание, отказы.

Сети и базы тут нет: проверяем сам слой. Ключевое, ради чего он писался, — что значение
нельзя переставить в другую запись или в другое поле, а испорченный шифртекст даёт
понятный отказ, а не мусор.
"""

from __future__ import annotations

import base64
import os

import pytest

from src.modules.core_connectors.access import crypto
from src.modules.core_connectors.errors import AccessUndecryptable

pytestmark = pytest.mark.pure


def _sealed(access_id: int = 1, field_key: str = "api_key", plain: str = "sk-live-42"):
    wrapped, version = crypto.new_data_key()
    data_key = crypto.unwrap_data_key(wrapped, version)
    stored = crypto.encrypt_value(
        plain, data_key=data_key, access_id=access_id, field_key=field_key, key_version=version
    )
    return stored, data_key


def test_round_trip_returns_the_same_value(master_key):
    stored, data_key = _sealed()

    assert stored.startswith("v1.")  # префикс = признак «зашифровано»
    assert "sk-live-42" not in stored
    assert (
        crypto.decrypt_value(stored, data_key=data_key, access_id=1, field_key="api_key")
        == "sk-live-42"
    )


def test_value_moved_to_another_record_does_not_open(master_key):
    stored, data_key = _sealed(access_id=1)

    with pytest.raises(AccessUndecryptable):
        crypto.decrypt_value(stored, data_key=data_key, access_id=2, field_key="api_key")


def test_value_moved_to_another_field_does_not_open(master_key):
    stored, data_key = _sealed(field_key="api_key")

    with pytest.raises(AccessUndecryptable):
        crypto.decrypt_value(
            stored, data_key=data_key, access_id=1, field_key="management_api_key"
        )


def test_truncated_ciphertext_is_a_typed_refusal(master_key):
    stored, data_key = _sealed()

    with pytest.raises(AccessUndecryptable):
        crypto.decrypt_value(
            stored[:-6], data_key=data_key, access_id=1, field_key="api_key"
        )


def test_another_master_key_cannot_unwrap_the_record_key(master_key, monkeypatch):
    wrapped, version = crypto.new_data_key()

    another = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    monkeypatch.setattr(crypto, "configured_master_key", lambda: another)

    with pytest.raises(AccessUndecryptable):
        crypto.unwrap_data_key(wrapped, version)


def test_empty_value_stays_empty(master_key):
    _, data_key = _sealed()

    stored = crypto.encrypt_value(
        "", data_key=data_key, access_id=1, field_key="api_key", key_version="v"
    )

    assert stored == ""  # шифровать нечего — пусто остаётся пустым


def test_plain_text_is_read_as_is(master_key):
    _, data_key = _sealed()

    # Значения без префикса — наследие незашифрованной базы: читаются как есть,
    # поэтому шифрование включается на живой базе без миграции данных.
    assert (
        crypto.decrypt_value("plain-token", data_key=data_key, access_id=1, field_key="api_key")
        == "plain-token"
    )


def test_without_a_master_key_encryption_is_simply_off(monkeypatch):
    monkeypatch.setattr(crypto, "configured_master_key", lambda: "")

    assert crypto.encryption_enabled() is False
    with pytest.raises(AccessUndecryptable):
        crypto.new_data_key()  # ключа нет — заводить конверт не из чего


def test_key_version_is_derived_from_the_key_itself(master_key):
    _, version = crypto.new_data_key()
    _, version_again = crypto.new_data_key()

    assert version == version_again  # версия — свойство мастер-ключа, а не записи
    assert len(version) == 8


def test_a_malformed_master_key_is_a_typed_refusal(monkeypatch):
    # Опечатка в .env не должна ронять запрос: это тот же «не расшифровывается»,
    # который наверху превращается в статус записи
    monkeypatch.setattr(crypto, "configured_master_key", lambda: "too-short")

    with pytest.raises(AccessUndecryptable):
        crypto.new_data_key()
