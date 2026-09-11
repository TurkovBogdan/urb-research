"""Чтение/запись ``.env`` с сохранением комментариев и структуры.

Запись правит строки ``KEY=…`` НА МЕСТЕ; комментарии, пустые строки и порядок не
трогаются. Отсутствующие ключи дописываются в конец. Чтение берёт значения прямо из
файла (источник, который и редактируется), а не из ``Config`` — форма показывает
ровно то, что в ``.env``, без валидации промежуточных состояний.

Здесь же установка **выписывает себе секреты сама** (``SECRETS``): токен MCP-поверхности
и мастер-ключ шифрования значений в БД. Оба нужны с первого старта, оба бессмысленно
требовать от человека — он всё равно сгенерирует случайную строку. Дом у этого кода
такой, потому что предмет модуля — сам файл ``.env``: чей ключ туда попадает, вопрос
второй.
"""

from __future__ import annotations

import base64
import fcntl
import os
import re
import secrets
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.core.config import Config, _env_file, get_config
from src.core.loggers import get_logger
from src.modules.core_setup.keys import FIELDS, SetupField

_SECRET_BYTES = 32
_LOG = get_logger("core_setup")


@dataclass(frozen=True)
class GeneratedSecret:
    """Секрет, который установка выписывает себе сама, если его ещё нет."""

    key: str
    generate: Callable[[], str]
    comment: str


def _bearer_token() -> str:
    return secrets.token_urlsafe(_SECRET_BYTES)


def _master_key() -> str:
    """32 случайных байта в base64url — формат, который ждёт слой шифрования."""
    return base64.urlsafe_b64encode(os.urandom(_SECRET_BYTES)).decode().rstrip("=")


SECRETS: tuple[GeneratedSecret, ...] = (
    GeneratedSecret(
        "MCP_TOKEN",
        _bearer_token,
        "# Статичный bearer MCP-серверов. Сгенерирован при первом старте.",
    ),
    GeneratedSecret(
        "SECRETS_KEY",
        _master_key,
        "# Мастер-ключ шифрования значений в БД. Сгенерирован при первом старте;\n"
        "# без него копия базы бесполезна, при его утрате доступы вводятся заново.",
    ),
)


def env_path() -> Path:
    return _env_file()


def _config_default(field: SetupField, config: Config) -> str:
    """Дефолт поля из ``Config``: ENV-ключ формы == поле Config в нижнем регистре
    (конвенция pydantic-settings — имя поля задаёт ENV-переменную)."""
    value = getattr(config, field.key.lower())
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def seed_defaults_if_absent(config: Config) -> bool:
    """Первый запуск без ``.env`` → создать его со значениями по умолчанию из
    ``Config`` (страница настроек показывает реальные дефолты, а не пустые поля).
    Секреты досыпает ``ensure_generated``, вызываемая следом. Возвращает True, если
    файл был создан."""
    if env_path().is_file():
        return False
    write_values({f.key: _config_default(f, config) for f in FIELDS})
    _restrict_access()
    return True


def _assignment_key(line: str) -> str | None:
    """Ключ строки ``KEY=value`` (без коммента/пробелов); None — если это не присваивание."""
    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
    return match.group(1) if match else None


def read_values(keys: Iterable[str]) -> dict[str, str]:
    """Текущие значения перечисленных ключей из ``.env`` (отсутствующие → пропущены)."""
    wanted = set(keys)
    values: dict[str, str] = {}
    path = env_path()
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        key = _assignment_key(line)
        if key in wanted:
            values[key] = line.split("=", 1)[1].strip()
    return values


def write_values(updates: Mapping[str, str], comments: Mapping[str, str] | None = None) -> None:
    """Записать значения в ``.env``: заменить строки ``KEY=`` на месте, недостающие — в конец.

    ``comments`` печатается только над **дописанными** ключами: файл читают глазами, и
    ключ, появившийся сам по себе, без объяснения выглядит как мусор.
    """
    if not updates:
        return
    path = env_path()
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    remaining = dict(updates)
    for i, line in enumerate(lines):
        key = _assignment_key(line)
        if key in remaining:
            lines[i] = f"{key}={remaining.pop(key)}"
    for key, value in remaining.items():
        comment = (comments or {}).get(key)
        if comment:
            lines.extend(["", *comment.splitlines()])
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _restrict_access() -> None:
    """Права 600 на ``.env``: в нём лежат секреты, читать их должен только владелец."""
    path = env_path()
    if path.is_file():
        path.chmod(0o600)


@contextmanager
def _write_lock() -> Iterator[None]:
    """Взаимное исключение на запись ``.env`` между процессами установки.

    Backend, worker и порождённый шимом второй backend стартуют одновременно; без
    блокировки двое могли бы сгенерировать РАЗНЫЕ ключи, а в файл лёг бы один — второй
    зашифровал бы записи ключом, которого больше нет.
    """
    lock_path = env_path().with_suffix(env_path().suffix + ".lock")
    with open(lock_path, "w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def ensure_generated(config: Config) -> list[str]:
    """Досыпать в ``.env`` секреты, которых в нём ещё нет. Возвращает сгенерированные ключи.

    Проверяется **эффективное** значение (``Config`` уже учёл и переменную оболочки, и
    файл): заданный оператором ключ не трогаем никогда. Порядок «сначала записать, потом
    принять» обязателен — ключ, оставшийся только в памяти, зашифровал бы записи так, что
    после перезапуска их никто не прочтёт; поэтому при сбое записи мы просто живём без него.
    """
    missing = [s for s in SECRETS if not _effective(config, s.key)]
    if not missing:
        return []

    written: list[str] = []
    with _write_lock():
        for secret in missing:
            if read_values([secret.key]).get(secret.key):
                continue  # пока ждали блокировку, ключ выписал соседний процесс
            value = secret.generate()
            try:
                write_values({secret.key: value}, comments={secret.key: secret.comment})
                _restrict_access()
            except OSError as exc:
                _LOG.warning("%s не записан в .env (%s) — работаем без него", secret.key, exc)
                continue
            os.environ[secret.key] = value
            written.append(secret.key)
    if written:
        get_config.cache_clear()
    return written


def _effective(config: Config, key: str) -> str:
    """Текущее значение ключа с точки зрения приложения (окружение поверх файла)."""
    return str(getattr(config, key.lower(), "") or "")


__all__ = [
    "SECRETS",
    "GeneratedSecret",
    "env_path",
    "ensure_generated",
    "read_values",
    "seed_defaults_if_absent",
    "write_values",
]
