"""ORM ``research_area`` — область (направление/раздел) внутри исследования.

FK ``research_code`` → ``research_index.code``. Знаниевый под-артефакт по общему паттерну
``title`` / ``description`` / ``body`` (как ``research_index`` и ``research_note``):

- **скан-слой** (для списка из N областей): ``title`` / ``description`` — «что это».
- **бриф** (перед ``body``): ``objective`` (чего добиться и зачем), ``scope`` (границы — что
  входит и что исключено), ``expectations`` (ожидаемая форма результата).
- **результат**: ``body`` (markdown-синтез раздела).

Области упорядочены по ``created_at``. Размеры title/description/brief режутся усечением в CRUD
(не ошибкой) по code points — см. ``crud/area.py``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now
from src.modules.research.constants import (
    AREA_BRIEF_MAX,
    AREA_DESCRIPTION_MAX,
    AREA_TITLE_MAX,
)


class ResearchArea(Base):
    __tablename__ = "research_area"
    __table_args__ = (Index("ix_research_area_research_code", "research_code"),)

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    research_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_index.code", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(AREA_TITLE_MAX))
    description: Mapped[str] = mapped_column(
        String(AREA_DESCRIPTION_MAX), default="", server_default=text("''")
    )
    objective: Mapped[str] = mapped_column(String(AREA_BRIEF_MAX), default="", server_default=text("''"))
    scope: Mapped[str] = mapped_column(String(AREA_BRIEF_MAX), default="", server_default=text("''"))
    expectations: Mapped[str] = mapped_column(String(AREA_BRIEF_MAX), default="", server_default=text("''"))
    body: Mapped[str] = mapped_column(Text, default="", server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


__all__ = ["ResearchArea"]
