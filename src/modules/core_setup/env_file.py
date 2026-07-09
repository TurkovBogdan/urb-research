"""Чтение/запись ``.env`` с сохранением комментариев и структуры.

Запись правит строки ``KEY=…`` НА МЕСТЕ; комментарии, пустые строки и порядок не
трогаются. Отсутствующие ключи дописываются в конец. Чтение берёт значения прямо из
файла (источник, который и редактируется), а не из ``Config`` — форма показывает
ровно то, что в ``.env``, без валидации промежуточных состояний.
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Iterable, Mapping
from pathlib import Path

from src.core.config import Config, _env_file
from src.modules.core_setup.keys import FIELDS, SetupField

_MCP_TOKEN_KEY = "MCP_TOKEN"
_MCP_TOKEN_BYTES = 32


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
    Заодно генерирует ``MCP_TOKEN`` — статический bearer MCP-серверов (пусто =
    allow-all), чтобы поверхность ``/mcp/<code>`` была защищена с первого старта.
    Возвращает True, если файл был создан."""
    if env_path().is_file():
        return False
    seeded = {f.key: _config_default(f, config) for f in FIELDS}
    seeded[_MCP_TOKEN_KEY] = secrets.token_urlsafe(_MCP_TOKEN_BYTES)
    write_values(seeded)
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


def write_values(updates: Mapping[str, str]) -> None:
    """Записать значения в ``.env``: заменить строки ``KEY=`` на месте, недостающие — в конец."""
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
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["env_path", "read_values", "seed_defaults_if_absent", "write_values"]
