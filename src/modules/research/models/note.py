"""ORM ``research_note`` — типизированная заметка исследования (мини-артефакт).

Заметка — не структура вывода (это область), а самостоятельный знаниевый мини-артефакт
рабочей памяти: то, что агент фиксирует по ходу и что не привязано ни к одному документу,
ни к одному разделу. Типовые поля описания как у ``research_index`` — ``title`` (≤128),
``description`` (краткое «что это», ≤512), ``body`` (основное тело, markdown, без лимита) —
плюс обязательный ``kind`` (``NOTE_KINDS``): тип заставляет отделить вывод от гипотезы от
вопроса от наблюдения от решения («схема как промпт»). Привязка только к исследованию
(``research_code`` → ``research_index.code``); порядок хронологический (``created_at``).

Размеры title/description режутся усечением в CRUD (кириллица-safe) — см. ``crud/note.py``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now
from src.modules.research.constants import (
    NOTE_DESCRIPTION_MAX,
    NOTE_KINDS,
    NOTE_TITLE_MAX,
    sql_in,
)


class ResearchNote(Base):
    __tablename__ = "research_note"
    __table_args__ = (
        CheckConstraint(f"kind IN ({sql_in(NOTE_KINDS)})", name="ck_research_note_kind"),
        Index("ix_research_note_research_code", "research_code"),
    )

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    research_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_index.code", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(NOTE_TITLE_MAX))
    description: Mapped[str] = mapped_column(
        String(NOTE_DESCRIPTION_MAX), default="", server_default=text("''")
    )
    body: Mapped[str] = mapped_column(Text, default="", server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


__all__ = ["ResearchNote"]
