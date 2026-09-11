"""``core_interface_settings`` — одна строка на одну отклонённую от умолчания настройку.

Единственная таблица модуля. Ключи, типы и умолчания объявлены в ``registry.py``; здесь
лежат только значения, и только те, что человек изменил, — отсутствие строки означает
умолчание из кода.

Колонки владельца нет: приложение рассчитано на одного пользователя без учётных записей,
и пустая колонка была бы враньём в схеме.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import json_value, timestamp
from src.modules.core_interface.constants import KEY_MAX_LENGTH


class InterfaceSetting(Base):
    __tablename__ = "core_interface_settings"

    key: Mapped[str] = mapped_column(String(KEY_MAX_LENGTH), primary_key=True)
    # ``NOT NULL`` намеренно: сброс к умолчанию удаляет строку, поэтому двух способов
    # сказать «умолчание» в таблице не бывает.
    value: Mapped[Any] = mapped_column(json_value())
    created_at: Mapped[datetime] = mapped_column(timestamp())
    updated_at: Mapped[datetime] = mapped_column(timestamp())


__all__ = ["InterfaceSetting"]
