"""ORM ``research_source_query`` — источниковый запрос (связь с системой поиска).

Создаётся при запуске поиска (``query_search_run``): привязывает исследование (``research_code``
→ ``research_index.code``) и конкретную область (``area_code`` → ``research_area.code``) к прогону
в web_search (``search_code`` → ``web_search_query.code``; мягкая cross-module ссылка, без FK).
``query`` — текст запроса (денормализация из web_search, чтобы читать без джойна). Поиск — **только
ссылки**: тела/синтеза у запроса нет. Статуса и lifecycle нет. Владеет источниками
(``research_source_document``). ``unique(area_code, search_code)`` — один web-прогон на область раз.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now


class ResearchSourceQuery(Base):
    __tablename__ = "research_source_query"
    __table_args__ = (
        UniqueConstraint(
            "area_code", "search_code", name="uq_research_source_query_area_search"
        ),
        Index("ix_research_source_query_research_code", "research_code"),
        Index("ix_research_source_query_area_code", "area_code"),
    )

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    research_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_index.code", ondelete="CASCADE")
    )
    area_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_area.code", ondelete="CASCADE")
    )
    search_code: Mapped[str] = mapped_column(String(25))
    query: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)


__all__ = ["ResearchSourceQuery"]
