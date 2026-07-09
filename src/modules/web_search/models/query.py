"""``web_search_query`` — один прогон поиска (NL) через движок.

ORM ``WebSearchQuery`` + её read-DTO (``QueryRow`` — тонкое зеркало строки; ``QueryDetail``
— строка с её выдачей) рядом. Первичный ключ — голый 22-hex код
(``crud.query.query_code``, случайный) — web_search коды не типизирует (агентская
презентация с префиксами живёт в модуле research). Дедупа нет: каждый прогон уникален. ``search_engine`` — движок, отдавший ссылки;
``fetch_engine`` — движок, которым тянули контент страниц (две разные функции). ``params``
(JSON) — параметры запроса (``max_results`` + include/exclude_domains, time_range). Машина
статусов ``pending → processing → done | error`` (синхронно, без ретраев); ``error`` — код
последней ошибки (nullable).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import CheckConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import json_value, timestamp
from src.core.utils.date import DatetimeUTCStr, utc_now
from src.modules.web_search.constants import (
    SEARCH_STATUS_PENDING,
    SEARCH_STATUSES,
    sql_in,
)
from src.modules.web_search.models.query_result import QueryResultView


class WebSearchQuery(Base):
    __tablename__ = "web_search_query"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({sql_in(SEARCH_STATUSES)})",
            name="ck_web_search_query_status",
        ),
        Index("ix_web_search_query_engine_status", "search_engine", "status"),
    )

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    search_engine: Mapped[str] = mapped_column(String(64))
    fetch_engine: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), server_default=SEARCH_STATUS_PENDING)
    query: Mapped[str] = mapped_column(Text)
    params: Mapped[Any | None] = mapped_column(json_value(), nullable=True)
    error: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(timestamp(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


class QueryRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    search_engine: str
    fetch_engine: str
    status: str
    query: str
    params: Any | None
    error: str | None
    finished_at: DatetimeUTCStr | None
    created_at: DatetimeUTCStr
    updated_at: DatetimeUTCStr


class QueryDetail(QueryRow):
    results: list[QueryResultView]


__all__ = ["WebSearchQuery", "QueryRow", "QueryDetail"]
