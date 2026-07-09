"""Per-module immutable store — codegen'd frozen dataclass из ModuleSchema."""

from __future__ import annotations

from dataclasses import make_dataclass
from typing import Any

from src.core.settings.fields import ListField, MultiChoiceField
from src.core.settings.schema import ModuleSchema


ModuleSettingsStore = Any
"""Тип per-module store. Конкретный класс кодогенерится в build_store."""


def _freeze(value: Any, field) -> Any:
    """list/multichoice → tuple, чтобы инстанс был полностью иммутабелен."""
    if isinstance(field, (ListField, MultiChoiceField)):
        return tuple(value)
    return value


def build_store(
    module: str,
    schema: ModuleSchema,
    values: dict[str, Any],
) -> ModuleSettingsStore:
    """Сконструировать frozen dataclass-инстанс из значений по схеме.

    Отсутствующие ключи заполняются ``field.default()`` (вызывающему положено
    логировать предупреждение в этом случае).
    """
    cls = make_dataclass(
        f"_{module.title().replace('_', '')}SettingsStore",
        [(f.key, Any) for f in schema],
        frozen=True,
    )
    kwargs = {}
    for f in schema:
        raw = values.get(f.key, f.default())
        kwargs[f.key] = _freeze(raw, f)
    return cls(**kwargs)


__all__ = ["ModuleSettingsStore", "build_store"]
