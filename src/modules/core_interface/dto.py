"""Тела запросов и ответов модуля.

Схема собирается из реестра на лету, поэтому отдельного хранения не требует и разойтись
с проверкой на записи не может.

Поле схемы называется наружу ``schema``, а внутри ``fields``: имя ``schema`` занято
методом самой ``BaseModel``, и поле с таким именем pydantic принимает лишь с руганью.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SettingSchemaOut(BaseModel):
    key: str
    type: str  # string | number | boolean
    default: Any
    options: list[Any] | None  # ``null`` — набор не ограничен


class InterfaceSettingsOut(BaseModel):
    """Действующие значения всех полей; схема — только по запросу старта."""

    values: dict[str, Any]
    fields: list[SettingSchemaOut] | None = Field(default=None, serialization_alias="schema")


class InterfaceSchemaOut(BaseModel):
    fields: list[SettingSchemaOut] = Field(serialization_alias="schema")


class InterfaceSettingsPatch(BaseModel):
    values: dict[str, Any]


class InterfaceSettingsReset(BaseModel):
    keys: list[str]


__all__ = [
    "InterfaceSchemaOut",
    "InterfaceSettingsOut",
    "InterfaceSettingsPatch",
    "InterfaceSettingsReset",
    "SettingSchemaOut",
]
