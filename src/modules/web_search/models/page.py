"""``web_search_page`` — контент страницы (документ поиска).

ORM ``WebSearchPage`` + её read-DTO (``PageRow`` — зеркало строки без тяжёлого контента;
``PageDetail`` — с ``body``) рядом. Первичный ключ — голый 22-hex код
(``crud.page.page_code``): хеш **детерминирован** от нормализованного url, поэтому код =
ключ дедупа по url (web_search коды не типизирует — префиксы живут в research). Хранится
только обработанный ``body`` (markdown) + ``body_hash`` для change-detection (raw не
храним). ``fetch_engine`` — движок, которым тянули (или потянут) контент (nullable — страница
создаётся до фетча и переиспользуется по дедупу; нужен для per-engine учёта фетча).
``title`` — заголовок документа (свойство самой страницы, независимое от запроса; берётся из
выдачи поиска при создании — первый нашедший движок задаёт, дедуп не перетирает). Машина
статусов ``pending`` (создана) → ``processing`` (идёт получение) → ``done``
(контент получен) / ``error`` (фетч упал — терминально, без повторов). ``error`` — код
последней ошибки. Ретраев нет.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import CheckConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import DatetimeUTCStr, utc_now
from src.modules.web_search.constants import (
    FETCH_STATUS_PENDING,
    FETCH_STATUSES,
    sql_in,
)


class WebSearchPage(Base):
    __tablename__ = "web_search_page"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({sql_in(FETCH_STATUSES)})",
            name="ck_web_search_page_status",
        ),
        Index("ix_web_search_page_status", "status"),
    )

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), server_default=FETCH_STATUS_PENDING)
    fetch_engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_hash: Mapped[str | None] = mapped_column(String(22), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(timestamp(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


class PageRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    status: str
    domain: str | None
    url: str
    title: str | None
    body_hash: str | None
    error: str | None
    fetched_at: DatetimeUTCStr | None
    created_at: DatetimeUTCStr
    updated_at: DatetimeUTCStr


class PageDetail(PageRow):
    body: str | None


__all__ = ["WebSearchPage", "PageRow", "PageDetail"]
