"""ORM ``research_group`` — группа исследований (справочник для раскладки реестра).

Человеческая раскладка реестра, а не часть пайплайна: группа не влияет ни на поиск, ни на
источники — она отвечает на вопрос «где это лежит». Исследование ссылается на неё колонкой
``research_index.group_code`` (nullable → ``NULL`` = не разложено); группы по умолчанию нет.

Поля — минимальный набор карточки: ``title`` / ``description`` (что это), ``icon`` (имя иконки
tabler в kebab-форме, ``''`` = не выбрана → фронт рисует запасную), ``color`` (имя тона из
палитры, ``''`` = не выбран → фронт красит акцентом) и ``sort``. Порядок вывода —
``sort`` по убыванию, затем ``title``: **больший sort = выше**, а второй ключ обязателен, иначе
группы с одинаковым sort (по умолчанию у всех ``GROUP_SORT_DEFAULT``) меняются местами между
запросами. Ни иконка, ни цвет не валидируются в БД: канонические наборы имён лежат в ``icons.py``
и ``colors.py``, а рисовать их умеет только фронт — проверка на записи превратила бы расширение
палитры в правку двух файлов на двух языках.

PK — голый 22-hex код (``random_hash()``); тип-префикс ``GROUP@`` надевается на границе
(см. ``research.codes``), в БД не хранится. Размеры title/description режутся усечением в CRUD.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import timestamp
from src.core.utils.date import utc_now
from src.modules.research.constants import (
    GROUP_COLOR_MAX,
    GROUP_DESCRIPTION_MAX,
    GROUP_ICON_MAX,
    GROUP_SORT_DEFAULT,
    GROUP_TITLE_MAX,
)


class ResearchGroup(Base):
    __tablename__ = "research_group"

    code: Mapped[str] = mapped_column(String(25), primary_key=True)
    title: Mapped[str] = mapped_column(String(GROUP_TITLE_MAX))
    description: Mapped[str] = mapped_column(
        String(GROUP_DESCRIPTION_MAX), default="", server_default=text("''")
    )
    icon: Mapped[str] = mapped_column(
        String(GROUP_ICON_MAX), default="", server_default=text("''")
    )
    color: Mapped[str] = mapped_column(
        String(GROUP_COLOR_MAX), default="", server_default=text("''")
    )
    sort: Mapped[int] = mapped_column(
        Integer, default=GROUP_SORT_DEFAULT, server_default=text(str(GROUP_SORT_DEFAULT))
    )
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


__all__ = ["ResearchGroup"]
