"""Public API подсистемы runtime user-tunable settings.

Re-exports типов полей и аксессор актуального per-module store. Внутренности
разнесены по модулям пакета (поля, схема, store, реестр, bootstrap, api).
"""

from __future__ import annotations

from typing import Any

from src.core.settings.fields import (
    BoolField,
    ChoiceField,
    DateField,
    DateTimeField,
    Field,
    FloatField,
    IntField,
    ListField,
    MultiChoiceField,
    StrField,
)
from src.core.settings.registry import get_registry
from src.core.settings.schema import ModuleSchema


def get_module_store(module: str) -> Any:
    """Текущий immutable store модуля. RuntimeError, если ещё не загружен."""
    return get_registry().get(module)


__all__ = [
    "BoolField",
    "ChoiceField",
    "DateField",
    "DateTimeField",
    "Field",
    "FloatField",
    "IntField",
    "ListField",
    "ModuleSchema",
    "MultiChoiceField",
    "StrField",
    "get_module_store",
]
