"""Schema = упорядоченный tuple полей одного модуля.

``validate_schema`` зовётся при регистрации модуля в реестре (build phase):
любая ошибка — fail-fast.
"""

from __future__ import annotations

import re

from src.core.settings.fields import Field


ModuleSchema = tuple[Field, ...]

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_schema(module: str, fields: ModuleSchema) -> None:
    """Уникальность ключей, snake_case, default валидируется ограничениями."""
    seen: set[str] = set()
    for f in fields:
        if not _KEY_RE.fullmatch(f.key):
            raise ValueError(
                f"{module}: invalid key {f.key!r} (expected snake_case)"
            )
        if f.key in seen:
            raise ValueError(f"{module}: duplicate key {f.key!r}")
        seen.add(f.key)
        try:
            f.validate(f.default())
        except ValueError as exc:
            raise ValueError(
                f"{module}.{f.key}: default fails own validation: {exc}"
            ) from exc

    _validate_visibility(module, fields)


def _validate_visibility(module: str, fields: ModuleSchema) -> None:
    """Условие видимости обязано ссылаться на существующее поле того же модуля.

    Опечатка в ключе иначе прошла бы молча и увела поле с экрана навсегда: значение при
    этом продолжало бы применяться, а править его стало бы нечем.
    """
    keys = {f.key for f in fields}
    for f in fields:
        if f.visible_when is None:
            continue
        if f.visible_when.key not in keys:
            raise ValueError(
                f"{module}.{f.key}: visible_when points at unknown key "
                f"{f.visible_when.key!r}"
            )
        if f.visible_when.key == f.key:
            raise ValueError(
                f"{module}.{f.key}: visible_when points at the field itself"
            )


def field_by_key(fields: ModuleSchema, key: str) -> Field:
    for f in fields:
        if f.key == key:
            return f
    raise KeyError(key)


__all__ = ["ModuleSchema", "validate_schema", "field_by_key"]
