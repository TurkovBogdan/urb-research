"""``web_search_query_result`` — результаты запроса: связь запрос ↔ документ (URL).

ORM ``WebSearchQueryResult`` + её read-DTO ``QueryResultView`` (строка выдачи, обогащённая
полями страницы) рядом. Внутренняя таблица-связка (нейронка на неё не ссылается) —
оставляет суррогатный ``id``. FK на строковые коды: ``query_code`` →
``web_search_query.code``, ``page_code`` → ``web_search_page.code`` (голые 22-hex хеши).
``summary`` — краткое содержание страницы в контексте запроса (общее для всех движков:
Tavily ``content``, Firecrawl ``description``, xAI — поле строгого вывода). Заголовок
документа — на самой странице (``web_search_page.title``), не тут: он свойство страницы, не
запроса. ``meta`` — остаточные контекстные поля движка (reason, favicon, …). ``unique
(query_code, page_code)`` — без дублей документа в одном запросе.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import json_value, timestamp
from src.core.utils.date import DatetimeUTCStr, utc_now


class WebSearchQueryResult(Base):
    __tablename__ = "web_search_query_result"
    __table_args__ = (
        UniqueConstraint(
            "query_code", "page_code", name="uq_web_search_query_result_query_page"
        ),
        Index("ix_web_search_query_result_query_code", "query_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    query_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("web_search_query.code", ondelete="CASCADE")
    )
    page_code: Mapped[str] = mapped_column(
        String(25), ForeignKey("web_search_page.code", ondelete="CASCADE")
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[Any | None] = mapped_column(json_value(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)


class QueryResultView(BaseModel):
    """Строка выдачи запроса + поля её страницы (для детальной запроса)."""

    page_code: str
    rank: int | None
    score: float | None
    summary: str | None
    meta: Any | None
    page_url: str
    page_title: str | None
    page_domain: str | None
    page_status: str
    page_fetched_at: DatetimeUTCStr | None


__all__ = ["WebSearchQueryResult", "QueryResultView"]
