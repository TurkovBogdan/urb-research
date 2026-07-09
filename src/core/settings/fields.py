"""Field classes for the runtime settings subsystem.

Каждое поле описывает один user-tunable параметр модуля. Поле:
- хранит метаданные (label, description, default, ограничения, UI-hints);
- умеет parse/serialize TEXT ↔ python value (для хранения в БД);
- валидирует значение через ``validate(value)``;
- декларирует свой UI через ``ui_descriptor()``.

Все поля frozen-dataclass'ы — список схемы хешируем, поля попадают в кеш
без сюрпризов.

Конструкторы используют ``object.__setattr__`` для нормализации входных
структур (``options`` → tuple-of-tuples и т.п.), потому что фабрики ``Field``
работают через ``__post_init__`` поверх ``frozen=True``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, ClassVar


# ── Base ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Field(ABC):
    """Базовый класс поля настройки."""

    key: str
    label: str
    description: str = ""

    kind: ClassVar[str] = ""

    @abstractmethod
    def python_type(self) -> type: ...

    @abstractmethod
    def default(self) -> Any:
        """Свежий default. Для list/multichoice — новый список на каждый вызов."""

    @abstractmethod
    def parse(self, text: str) -> Any:
        """TEXT → python value. Может бросить ValueError."""

    @abstractmethod
    def serialize(self, value: Any) -> str:
        """python value → TEXT для хранения в БД."""

    @abstractmethod
    def validate(self, value: Any) -> None:
        """Проверка значения. На неуспех — ValueError с понятным сообщением."""

    @abstractmethod
    def ui_descriptor(self) -> dict[str, Any]:
        """Описатель поля для UI."""

    def is_secret(self) -> bool:
        """Секрет (токен/пароль): маскируется на чтение, не логируется."""
        return False

    def repr_for_log(self, value: Any) -> str:
        return "***" if self.is_secret() else repr(value)

    def _base_ui(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "kind": self.kind,
            "label": self.label,
            "description": self.description,
            "default": self.default(),
        }


# ── Int / Float ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IntField(Field):
    default_: int = 0
    min: int | None = None
    max: int | None = None

    kind: ClassVar[str] = "int"

    def python_type(self) -> type:
        return int

    def default(self) -> int:
        return self.default_

    def parse(self, text: str) -> int:
        return int(text)

    def serialize(self, value: Any) -> str:
        return str(int(value))

    def validate(self, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{self.key}: expected int")
        if self.min is not None and value < self.min:
            raise ValueError(f"{self.key}: value < min ({self.min})")
        if self.max is not None and value > self.max:
            raise ValueError(f"{self.key}: value > max ({self.max})")

    def ui_descriptor(self) -> dict[str, Any]:
        return {**self._base_ui(), "min": self.min, "max": self.max}


@dataclass(frozen=True)
class FloatField(Field):
    default_: float = 0.0
    min: float | None = None
    max: float | None = None
    step: float = 0.1
    decimals: int = 2

    kind: ClassVar[str] = "float"

    def python_type(self) -> type:
        return float

    def default(self) -> float:
        return float(self.default_)

    def parse(self, text: str) -> float:
        return float(text)

    def serialize(self, value: Any) -> str:
        return str(float(value))

    def validate(self, value: Any) -> None:
        if isinstance(value, bool):
            raise ValueError(f"{self.key}: expected float")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{self.key}: expected float")
        v = float(value)
        if self.min is not None and v < self.min:
            raise ValueError(f"{self.key}: value < min ({self.min})")
        if self.max is not None and v > self.max:
            raise ValueError(f"{self.key}: value > max ({self.max})")

    def ui_descriptor(self) -> dict[str, Any]:
        return {
            **self._base_ui(),
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "decimals": self.decimals,
        }


# ── Bool ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BoolField(Field):
    default_: bool = False

    kind: ClassVar[str] = "bool"

    def python_type(self) -> type:
        return bool

    def default(self) -> bool:
        return self.default_

    def parse(self, text: str) -> bool:
        return text == "true"

    def serialize(self, value: Any) -> str:
        if not isinstance(value, bool):
            raise ValueError(f"{self.key}: expected bool")
        return "true" if value else "false"

    def validate(self, value: Any) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"{self.key}: expected bool")

    def ui_descriptor(self) -> dict[str, Any]:
        return self._base_ui()


# ── Str ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class StrField(Field):
    default_: str = ""
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    lines: int = 1
    secret: bool = False

    kind: ClassVar[str] = "str"

    def python_type(self) -> type:
        return str

    def is_secret(self) -> bool:
        return self.secret

    def default(self) -> str:
        return self.default_

    def parse(self, text: str) -> str:
        return text

    def serialize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{self.key}: expected str")
        return value

    def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValueError(f"{self.key}: expected str")
        if self.min_length is not None and len(value) < self.min_length:
            raise ValueError(
                f"{self.key}: length < min_length ({self.min_length})"
            )
        if self.max_length is not None and len(value) > self.max_length:
            raise ValueError(
                f"{self.key}: length > max_length ({self.max_length})"
            )
        if self.pattern is not None:
            import re
            if not re.fullmatch(self.pattern, value):
                raise ValueError(f"{self.key}: does not match pattern")

    def ui_descriptor(self) -> dict[str, Any]:
        return {
            **self._base_ui(),
            "min_length": self.min_length,
            "max_length": self.max_length,
            "pattern": self.pattern,
            "lines": self.lines,
            "secret": self.secret,
        }


# ── Date / DateTime ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class DateField(Field):
    default_: date = field(default_factory=lambda: date(1970, 1, 1))
    min: date | None = None
    max: date | None = None

    kind: ClassVar[str] = "date"

    def python_type(self) -> type:
        return date

    def default(self) -> date:
        return self.default_

    def parse(self, text: str) -> date:
        return date.fromisoformat(text)

    def serialize(self, value: Any) -> str:
        if not isinstance(value, date) or isinstance(value, datetime):
            raise ValueError(f"{self.key}: expected date")
        return value.isoformat()

    def validate(self, value: Any) -> None:
        if not isinstance(value, date) or isinstance(value, datetime):
            raise ValueError(f"{self.key}: expected date")
        if self.min is not None and value < self.min:
            raise ValueError(f"{self.key}: value < min ({self.min})")
        if self.max is not None and value > self.max:
            raise ValueError(f"{self.key}: value > max ({self.max})")

    def ui_descriptor(self) -> dict[str, Any]:
        return {**self._base_ui(), "min": self.min, "max": self.max}


@dataclass(frozen=True)
class DateTimeField(Field):
    default_: datetime = field(default_factory=lambda: datetime(1970, 1, 1))
    min: datetime | None = None
    max: datetime | None = None

    kind: ClassVar[str] = "datetime"

    def python_type(self) -> type:
        return datetime

    def default(self) -> datetime:
        return self._naive(self.default_)

    def parse(self, text: str) -> datetime:
        return self._naive(datetime.fromisoformat(text))

    def serialize(self, value: Any) -> str:
        if not isinstance(value, datetime):
            raise ValueError(f"{self.key}: expected datetime")
        return self._naive(value).isoformat()

    def validate(self, value: Any) -> None:
        if not isinstance(value, datetime):
            raise ValueError(f"{self.key}: expected datetime")
        v = self._naive(value)
        if self.min is not None and v < self._naive(self.min):
            raise ValueError(f"{self.key}: value < min ({self.min})")
        if self.max is not None and v > self._naive(self.max):
            raise ValueError(f"{self.key}: value > max ({self.max})")

    def ui_descriptor(self) -> dict[str, Any]:
        return {**self._base_ui(), "min": self.min, "max": self.max}

    @staticmethod
    def _naive(value: datetime) -> datetime:
        if value.tzinfo is not None:
            from datetime import timezone
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


# ── Choice ──────────────────────────────────────────────────────────────


def _normalize_options(
    options: Mapping[str, str] | Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if isinstance(options, Mapping):
        return tuple((str(k), str(v)) for k, v in options.items())
    return tuple((str(k), str(v)) for k, v in options)


@dataclass(frozen=True)
class ChoiceField(Field):
    default_: str = ""
    options: tuple[tuple[str, str], ...] = ()

    kind: ClassVar[str] = "choice"

    def __post_init__(self) -> None:
        object.__setattr__(self, "options", _normalize_options(self.options))

    def python_type(self) -> type:
        return str

    def default(self) -> str:
        return self.default_

    def parse(self, text: str) -> str:
        return text

    def serialize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{self.key}: expected str code")
        return value

    def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValueError(f"{self.key}: expected str code")
        if value not in {code for code, _ in self.options}:
            raise ValueError(f"{self.key}: unknown option {value!r}")

    def ui_descriptor(self) -> dict[str, Any]:
        return {
            **self._base_ui(),
            "options": [{"code": c, "label": l} for c, l in self.options],
        }


@dataclass(frozen=True)
class MultiChoiceField(Field):
    default_: tuple[str, ...] = ()
    options: tuple[tuple[str, str], ...] = ()
    min_items: int = 0
    max_items: int | None = None

    kind: ClassVar[str] = "multichoice"

    def __post_init__(self) -> None:
        object.__setattr__(self, "options", _normalize_options(self.options))
        object.__setattr__(self, "default_", tuple(self.default_))

    def python_type(self) -> type:
        return list

    def default(self) -> list[str]:
        return list(self.default_)

    def parse(self, text: str) -> list[str]:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError(f"{self.key}: expected JSON array")
        return [str(x) for x in data]

    def serialize(self, value: Any) -> str:
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{self.key}: expected list")
        return json.dumps(list(value), ensure_ascii=False)

    def validate(self, value: Any) -> None:
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{self.key}: expected list")
        known = {code for code, _ in self.options}
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"{self.key}: items must be str codes")
            if item not in known:
                raise ValueError(f"{self.key}: unknown option {item!r}")
        if len(value) < self.min_items:
            raise ValueError(
                f"{self.key}: items < min_items ({self.min_items})"
            )
        if self.max_items is not None and len(value) > self.max_items:
            raise ValueError(
                f"{self.key}: items > max_items ({self.max_items})"
            )

    def ui_descriptor(self) -> dict[str, Any]:
        return {
            **self._base_ui(),
            "options": [{"code": c, "label": l} for c, l in self.options],
            "min_items": self.min_items,
            "max_items": self.max_items,
        }


# ── List ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ListField(Field):
    item: Field | None = None
    default_: tuple[Any, ...] = ()
    min_items: int = 0
    max_items: int | None = None

    kind: ClassVar[str] = "list"

    def __post_init__(self) -> None:
        if self.item is None:
            raise ValueError(f"{self.key}: ListField requires item=Field(...)")
        object.__setattr__(self, "default_", tuple(self.default_))

    def python_type(self) -> type:
        return list

    def default(self) -> list[Any]:
        return list(self.default_)

    def parse(self, text: str) -> list[Any]:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError(f"{self.key}: expected JSON array")
        assert self.item is not None
        return [self.item.parse(x if isinstance(x, str) else str(x)) for x in data]

    def serialize(self, value: Any) -> str:
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{self.key}: expected list")
        assert self.item is not None
        encoded = [self.item.serialize(x) for x in value]
        return json.dumps(encoded, ensure_ascii=False)

    def validate(self, value: Any) -> None:
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{self.key}: expected list")
        assert self.item is not None
        for x in value:
            self.item.validate(x)
        if len(value) < self.min_items:
            raise ValueError(
                f"{self.key}: items < min_items ({self.min_items})"
            )
        if self.max_items is not None and len(value) > self.max_items:
            raise ValueError(
                f"{self.key}: items > max_items ({self.max_items})"
            )

    def ui_descriptor(self) -> dict[str, Any]:
        assert self.item is not None
        item_desc = self.item.ui_descriptor()
        item_desc.pop("key", None)
        item_desc.pop("label", None)
        item_desc.pop("description", None)
        item_desc.pop("default", None)
        return {
            **self._base_ui(),
            "min_items": self.min_items,
            "max_items": self.max_items,
            "item": item_desc,
        }


__all__ = [
    "Field",
    "IntField",
    "FloatField",
    "BoolField",
    "StrField",
    "DateField",
    "DateTimeField",
    "ChoiceField",
    "MultiChoiceField",
    "ListField",
]
