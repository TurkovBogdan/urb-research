"""ORM-модель строки таблицы ``core_modules_settings``."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp


class CoreModuleSetting(Base):
    __tablename__ = "core_modules_settings"

    module: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(timestamp())
    updated_at: Mapped[datetime] = mapped_column(timestamp())


__all__ = ["CoreModuleSetting"]
