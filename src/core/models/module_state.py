"""ORM-модель строки таблицы ``core_modules_state``.

Произвольное runtime-состояние модуля (курсоры импорта, счётчики, маркеры
запусков). Сосед ``core_modules_settings``, но для внутренних машинных данных,
а не пользовательского конфига: без схемы, реестра и UI. ``value`` — JSONB,
модуль кладёт структуру напрямую.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import json_value, timestamp


class CoreModuleState(Base):
    __tablename__ = "core_modules_state"

    module: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[Any] = mapped_column(json_value())
    created_at: Mapped[datetime] = mapped_column(timestamp())
    updated_at: Mapped[datetime] = mapped_column(timestamp())


__all__ = ["CoreModuleState"]
