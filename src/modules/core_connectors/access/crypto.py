"""Шифрование значений записи доступа: конверт поверх AES-256-GCM.

Гарантия одной фразой, и расширять её нельзя: шифрование делает бесполезными копию базы,
дамп и бэкап, уехавшие **без** мастер-ключа. От того, кто получил работающее приложение
или машину, оно не защищает — приложение и есть законный держатель ключа. Полный разбор с
моделью угроз — ``RESEARCH@29e8fbec1ace27c20b403c``.

Конверт: у каждой записи свой ключ данных, завёрнутый мастер-ключом и лежащий в её же
строке. Ротация мастер-ключа перезаворачивает короткие ключи и **не трогает значения**, а
компрометация одного ключа данных стоит одной записи.

Формат значения в колонке — ``v1.<версия ключа>.<base64url(nonce ‖ шифртекст ‖ тег)>``.
Префикс служит и признаком «зашифровано»: значения без него читаются как открытый текст,
поэтому шифрование включается на живой базе без миграции данных.

Связывание (AAD) — ``core_connectors_access | id записи | ключ поля | версия ключа``:
перенос значения в другую запись или в другое поле ломает проверку тега. Fernet для этого
не годится — у него нет связанных данных вовсе, и это проверено по его исходнику.

Версия мастер-ключа выводится из него самого (первые байты SHA-256), поэтому подменённый
ключ виден сразу и даёт статус «не расшифровывается» вместо мусора. Ротация с перекрытием
(старый ключ рядом с новым) опирается на тот же вывод версии — на сегодня установка
держит один ключ, ``_master_keys`` отдаёт словарь на одну запись.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.core.config import get_config
from src.modules.core_connectors.errors import AccessUndecryptable

CIPHER_VERSION = "v1"
TABLE = "core_connectors_access"

_NONCE_BYTES = 12
_KEY_BYTES = 32
_VERSION_CHARS = 8
_DATA_KEY_FIELD = "__data_key__"  # «поле» конверта: ключ записи связывается им же


def _decode_key(raw: str) -> bytes:
    """Мастер-ключ из окружения. Кривой ключ — тоже «не расшифровывается»: запись получает
    статус и причину, а не роняет запрос — иначе опечатка в ``.env`` кладёт весь раздел."""
    try:
        key = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    except (binascii.Error, ValueError) as exc:
        raise AccessUndecryptable(f"SECRETS_KEY не читается как base64url: {exc}") from exc
    if len(key) != _KEY_BYTES:
        raise AccessUndecryptable(
            f"SECRETS_KEY: ожидается {_KEY_BYTES} байта в base64url, получено {len(key)}"
        )
    return key


def _key_version(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:_VERSION_CHARS]


def configured_master_key() -> str:
    """Мастер-ключ установки строкой — единственная точка связи слоя с конфигурацией.

    Отдельной функцией, потому что подменить её в тесте — единственный честный способ
    задать «ключа нет»: у ``Config`` включён ``env_ignore_empty``, и пустая переменная
    окружения не перекрывает значение, а откатывается на строку из ``.env``.
    """
    return get_config().secrets_key.strip()


def _master_keys() -> dict[str, bytes]:
    """Мастер-ключи установки, ``версия → ключ``. Пусто = шифрование выключено."""
    raw = configured_master_key()
    if not raw:
        return {}
    key = _decode_key(raw)
    return {_key_version(key): key}


def encryption_enabled() -> bool:
    """Задан ли мастер-ключ. Пусто — законное состояние, а не ошибка старта."""
    return bool(configured_master_key())


def master_key_version() -> str:
    """Версия текущего мастер-ключа — то единственное про него, что можно писать в лог."""
    keys = _master_keys()
    return next(iter(keys), "")


def generate_master_key() -> str:
    """Новый мастер-ключ в том виде, в каком он кладётся в ``.env``."""
    return base64.urlsafe_b64encode(os.urandom(_KEY_BYTES)).decode().rstrip("=")


def _current_master() -> tuple[str, bytes]:
    keys = _master_keys()
    if not keys:
        raise AccessUndecryptable("Мастер-ключ не задан (SECRETS_KEY пуст)")
    version = next(iter(keys))
    return version, keys[version]


def _master_by_version(version: str) -> bytes:
    key = _master_keys().get(version)
    if key is None:
        raise AccessUndecryptable(
            f"Мастер-ключ версии {version!r} недоступен: ключа нет или он не тот"
        )
    return key


def _aad(access_id: int, field_key: str, key_version: str) -> bytes:
    return f"{TABLE}|{access_id}|{field_key}|{key_version}".encode()


def _seal(key: bytes, plain: str, aad: bytes, key_version: str) -> str:
    nonce = os.urandom(_NONCE_BYTES)
    sealed = nonce + AESGCM(key).encrypt(nonce, plain.encode(), aad)
    payload = base64.urlsafe_b64encode(sealed).decode().rstrip("=")
    return f"{CIPHER_VERSION}.{key_version}.{payload}"


def _open(key: bytes, stored: str, aad: bytes) -> str:
    _, _, payload = stored.split(".", 2)
    sealed = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    nonce, ciphertext = sealed[:_NONCE_BYTES], sealed[_NONCE_BYTES:]
    return AESGCM(key).decrypt(nonce, ciphertext, aad).decode()


def is_encrypted(stored: str) -> bool:
    """Зашифровано ли значение (по префиксу формата); остальное — открытый текст."""
    return stored.startswith(f"{CIPHER_VERSION}.")


def stored_key_version(stored: str) -> str:
    """Версия мастер-ключа, которой запечатано значение."""
    return stored.split(".", 2)[1]


def new_data_key() -> tuple[str, str]:
    """Ключ данных новой записи: завёрнутый мастер-ключом + версия этого мастер-ключа."""
    version, master = _current_master()
    data_key = os.urandom(_KEY_BYTES)
    aad = f"{TABLE}|{_DATA_KEY_FIELD}|{version}".encode()
    return _seal(master, base64.urlsafe_b64encode(data_key).decode(), aad, version), version


def unwrap_data_key(wrapped: str, key_version: str) -> bytes:
    """Развернуть ключ записи её мастер-ключом. Любой сбой — ``AccessUndecryptable``."""
    master = _master_by_version(key_version)
    aad = f"{TABLE}|{_DATA_KEY_FIELD}|{key_version}".encode()
    try:
        return base64.urlsafe_b64decode(_open(master, wrapped, aad))
    except (InvalidTag, ValueError, IndexError) as exc:
        raise AccessUndecryptable(f"Ключ записи не разворачивается: {exc}") from exc


def encrypt_value(
    plain: str, *, data_key: bytes, access_id: int, field_key: str, key_version: str
) -> str:
    """Запечатать значение поля записи. Пустая строка остаётся пустой — шифровать нечего."""
    if not plain:
        return ""
    return _seal(data_key, plain, _aad(access_id, field_key, key_version), key_version)


def decrypt_value(stored: str, *, data_key: bytes, access_id: int, field_key: str) -> str:
    """Развернуть значение поля. Открытый текст (без префикса) отдаётся как есть —
    так шифрование включается на живой базе без миграции данных.

    Версия для связывания берётся из **самого значения**, а не из строки записи: ротация
    мастер-ключа перезаворачивает ключ записи и меняет её ``key_version``, а значения
    остаются запечатанными тем же ключом данных и со своей версией в связанных данных.
    """
    if not stored or not is_encrypted(stored):
        return stored
    try:
        return _open(data_key, stored, _aad(access_id, field_key, stored_key_version(stored)))
    except (InvalidTag, ValueError, IndexError) as exc:
        raise AccessUndecryptable(f"Значение {field_key!r} не расшифровывается: {exc}") from exc


__all__ = [
    "CIPHER_VERSION",
    "configured_master_key",
    "encryption_enabled",
    "master_key_version",
    "generate_master_key",
    "is_encrypted",
    "stored_key_version",
    "new_data_key",
    "unwrap_data_key",
    "encrypt_value",
    "decrypt_value",
]
