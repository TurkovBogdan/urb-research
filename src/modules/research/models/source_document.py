"""ORM ``research_source_document`` — источник: ссылка на найденную страницу + оценка.

**Не хранит копию данных страницы.** url/domain/title/body берутся join'ом из
``web_search_page`` по ``page_code`` (мягкая cross-module ссылка, без FK — владеет
web_search). Локально — только связи (``research_code``/``area_code``/``query_code``) и
research-оценка: ``status`` (состояние в пайплайне), ``relevance`` (важность 1–10),
``summary`` (снимок саммери находки из ``web_search_query_result``), ``note`` (польза ИЛИ
причина отсева). ``unique(query_code, page_code)`` — один источник на пару «запрос×страница»
(один и тот же URL в разных исследованиях = разные строки, оценка изолирована).

Статусы (``DOC_STATUSES``): ``fetch_error`` (страница не загрузилась — держим ради
целостности) / ``pending`` (есть, не оценён) / ``kept`` (оставлен) / ``filtered`` (отсеян,
причина в ``note``). kept↔filtered — явное решение агента, relevance — отдельный балл.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now
from src.modules.research.constants import DOC_PENDING, DOC_STATUSES, sql_in


class ResearchSourceDocument(Base):
    __tablename__ = "research_source_document"
    __table_args__ = (
        UniqueConstraint(
            "query_code", "page_code", name="uq_research_source_document_query_page"
        ),
        CheckConstraint(
            f"status IN ({sql_in(DOC_STATUSES)})", name="ck_research_source_document_status"
        ),
        CheckConstraint(
            "relevance BETWEEN 1 AND 10", name="ck_research_source_document_relevance"
        ),
        Index("ix_research_source_document_query_code", "query_code"),
    )

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    research_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_index.code", ondelete="CASCADE")
    )
    area_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_area.code", ondelete="CASCADE")
    )
    query_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("research_source_query.code", ondelete="CASCADE")
    )
    page_code: Mapped[str] = mapped_column(String(25))
    status: Mapped[str] = mapped_column(String(16), server_default=DOC_PENDING)
    relevance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="", server_default=text("''"))
    note: Mapped[str] = mapped_column(Text, default="", server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


__all__ = ["ResearchSourceDocument"]
