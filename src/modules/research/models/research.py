"""ORM ``research_index`` — исследование (корень реестра).

Исследование — знаниевый артефакт: ``title`` (заголовок/название, до 128),
``description`` (краткое описание, до 512) и ``body`` (основное тело, без лимита,
markdown). Статуса нет — это не прогон, а документ; машина состояний живёт на уровне
запроса (``research_source_query``). Владеет запросами.

``group_code`` — группа, в которую входит исследование (``research_group.code``). Единственная
nullable-ссылка модуля, и это осознанно: ``NULL`` = не разложено, а пустая строка (обычная форма
«не задано» для текстовых полей research) в FK не резолвится. Группы по умолчанию нет.
``ON DELETE SET NULL`` описывает намерение, но на SQLite не сработает (FK-каскад выключен) —
отвязку при удалении группы делает CRUD, как и остальные каскады модуля.

PK — голый 22-hex код (``random_hash()``, ``String(25)`` со слаком). Тип-префикс
``RESEARCH@`` — презентация, надевается на границе (см. ``research.codes``), в БД не
хранится. Код случайный — дедупа по заголовку нет (одну тему можно исследовать заново →
новый артефакт = новый код).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now
from src.modules.research.constants import RESEARCH_DESCRIPTION_MAX


class Research(Base):
    __tablename__ = "research_index"

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    group_code: Mapped[str | None] = mapped_column(
        String(25),
        ForeignKey(
            "research_group.code", ondelete="SET NULL", name="fk_research_index_group_code"
        ),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(
        String(RESEARCH_DESCRIPTION_MAX), default="", server_default=text("''")
    )
    body: Mapped[str] = mapped_column(Text, default="", server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


__all__ = ["Research"]
