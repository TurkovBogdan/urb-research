"""Строка таблицы ↔ объект JSON: одно правило перевода на все девять таблиц архива.

Ключи объекта — имена колонок, значения — то, что переживает JSON: даты уезжают тем же
SQL-форматом, каким их отдаёт API (``DatetimeUTCStr``), JSON-колонки остаются объектами,
остальное копируется как есть. Отдельного описания на каждую таблицу нет намеренно: список
колонок уже есть в модели, и второй его экземпляр разъехался бы с первым на первой же
миграции.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime

from src.core.utils.date import datetime_from_agent, datetime_to_agent
from src.modules.research.transfer.errors import ArchiveError

_MISSING = object()


def row_to_json(row: Any, *, omit: tuple[str, ...] = ()) -> dict[str, Any]:
    """Строка ORM → объект архива (без перечисленных колонок)."""
    values: dict[str, Any] = {}
    for column in row.__table__.columns:
        if column.name in omit:
            continue
        value = getattr(row, column.name)
        values[column.name] = datetime_to_agent(value) if isinstance(value, datetime) else value
    return values


def json_to_values(model: Any, data: dict[str, Any], *, omit: tuple[str, ...] = ()) -> dict[str, Any]:
    """Объект архива → значения для вставки, по колонкам модели.

    Незнакомые ключи игнорируются (архив мог приехать с версии, где колонок больше), а
    недостающая колонка добирается умолчанием — но только если умолчание есть: колонка без
    умолчания и без значения означает архив, которому верить нельзя.
    """
    values: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name in omit:
            continue
        raw = data.get(column.name, _MISSING)
        if raw is _MISSING:
            values[column.name] = _fallback(model, column)
            continue
        values[column.name] = _parse(model, column, raw)
    return values


def same_moment(local: datetime | None, archived: datetime | None) -> bool:
    """Одно ли это время с точностью до секунды.

    Сравнивать напрямую нельзя: в архив время уезжает SQL-форматом без долей секунды, а SQLite
    хранит микросекунды, которые туда записал ``utc_now()``. На точном сравнении своя же запись
    после круга «экспорт → импорт» перестала бы опознаваться.
    """
    if local is None or archived is None:
        return local is archived
    return local.replace(microsecond=0) == archived.replace(microsecond=0)


def clip_to_columns(model: Any, values: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Подрезать строковые значения под ширину колонок; вернуть значения и имена усечённых.

    Политика та же, что у CRUD модуля (``_clip``): длинное название режется, а не роняет запись.
    Иначе исследование с длинным заголовком, приехавшее с версии с более широкой колонкой,
    упиралось бы в отказ там, где обычная правка через MCP просто обрезает.
    """
    clipped: list[str] = []
    for column in model.__table__.columns:
        limit = getattr(column.type, "length", None)
        value = values.get(column.name)
        if limit is None or not isinstance(value, str) or len(value) <= limit:
            continue
        values[column.name] = value[:limit]
        clipped.append(column.name)
    return values, clipped


def _fallback(model: Any, column: Any) -> Any:
    if column.nullable:
        return None
    default = getattr(column.default, "arg", None)
    if default is not None and not callable(default):
        return default
    raise ArchiveError(
        f"строка таблицы {model.__tablename__} не содержит обязательного поля «{column.name}»"
    )


def _parse(model: Any, column: Any, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(column.type, DateTime):
        try:
            return datetime_from_agent(value)
        except (TypeError, ValueError) as error:
            raise ArchiveError(
                f"поле «{column.name}» таблицы {model.__tablename__} не похоже на дату: {value!r}"
            ) from error
    return value


__all__ = ["clip_to_columns", "json_to_values", "row_to_json", "same_moment"]
