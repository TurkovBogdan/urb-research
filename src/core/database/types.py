"""Портируемые типы колонок: одна модель работает на PostgreSQL и SQLite.

PostgreSQL сохраняет богатые нативные типы через ``.with_variant()``; SQLite
(zero-install тир) откатывается на generic-базу. Эти хелперы делают **и миграции
портируемыми**: миграция, использующая их (``json_value()``/``timestamp()``), катится
как на PostgreSQL, так и на файловый SQLite (dev). ``create_all`` остаётся только для
in-memory SQLite (тест-харнес), у которого нет истории миграций.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.types import TypeEngine


def timestamp() -> TypeEngine[Any]:
    """Время без микросекунд: PG → ``TIMESTAMP(precision=0)``, SQLite → ``DATETIME``."""
    return DateTime().with_variant(TIMESTAMP(precision=0), "postgresql")


def json_value() -> TypeEngine[Any]:
    """Структурный JSON: PG → ``JSONB``, SQLite → ``JSON`` (хранится как TEXT)."""
    return JSON().with_variant(JSONB(), "postgresql")


__all__ = ["json_value", "timestamp"]
