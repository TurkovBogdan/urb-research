"""``core_connectors_access`` — запись доступа: чем мы ходим в конкретный сервис.

ORM + её read-DTO рядом. Единственная таблица модуля: паспорт коннектора — это код (он не
хранится и не редактируется), реестр — оперативная память процесса, мастер-ключ — окружение
установки. Поэтому добавление коннектора, поля, записи или ключа миграций не требует.

Одна колонка значений на всю запись, а не «секреты отдельно, параметры отдельно»: что из
полей секрет, знает паспорт, а два места для одной записи означали бы рассинхрон. Секретные
значения лежат шифртекстом (``access/crypto.py``), несекретные — как есть.

Имени у записи нет: запись опознаётся коннектором, а его имя живёт в паспорте. Своё название
понадобится в тот день, когда записей на один сервис станет несколько и их придётся
различать в списке — до тех пор это было бы поле, которое правится, но нигде не показано.

Ключ обычный числовой: типизированные коды вида ``TYPE@hash`` — принадлежность MCP-плоскости,
где агенту надо с одного взгляда отличить исследование от источника. У доступов агентской
поверхности нет.

Статус записи **вычисляется**, а не хранится: первые четыре диагноза считаются без единого
сетевого вызова (выключено → не настроено → не расшифровывается → готово), пятый (``error``)
появляется только по итогу живой проверки.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.runtime import Base
from src.core.database.types import json_value, timestamp
from src.core.utils.date import DatetimeUTCStr, utc_now
from src.modules.core_connectors.connectors.passport import ConnectorBalance

ACCESS_STATUS_DISABLED = "disabled"
ACCESS_STATUS_UNCONFIGURED = "unconfigured"
ACCESS_STATUS_UNDECRYPTABLE = "undecryptable"
ACCESS_STATUS_ERROR = "error"
ACCESS_STATUS_OK = "ok"

ACCESS_STATUSES = (
    ACCESS_STATUS_DISABLED,
    ACCESS_STATUS_UNCONFIGURED,
    ACCESS_STATUS_UNDECRYPTABLE,
    ACCESS_STATUS_ERROR,
    ACCESS_STATUS_OK,
)


class CoreConnectorsAccess(Base):
    __tablename__ = "core_connectors_access"
    __table_args__ = (Index("ix_core_connectors_access_connector", "connector"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    connector: Mapped[str] = mapped_column(String(64))
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    values: Mapped[dict] = mapped_column(json_value(), default=dict)
    data_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        timestamp(), default=utc_now, onupdate=utc_now
    )


class AccessStatus(BaseModel):
    status: str  # один из ACCESS_STATUSES
    detail: str | None = None  # причина, когда статус не ``ok``


class AccessRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enabled: bool
    connector: str
    connector_name: str  # имя из паспорта; пусто, если коннектор снят с регистрации
    is_default: bool
    status: AccessStatus
    created_at: DatetimeUTCStr
    updated_at: DatetimeUTCStr


class AccessDetail(AccessRow):
    """Строка + значения полей: секреты подменены сентинелом, несекретные — как есть."""

    values: dict[str, str]
    fields: list[dict] = []  # дескрипторы паспорта с признаком «задан» под форму записи


class AccessView(AccessRow):
    """Строка + то, что снимается вживую: ровно то, что рисует карточку сервиса.

    Проверка сюда не входит намеренно: она делается по кнопке (``POST /accesses/{id}/check``),
    а не при каждом показе списка — иначе на открытие страницы уходил бы второй веер
    сетевых вызовов поверх балансового.
    """

    has_balance: bool
    balance: ConnectorBalance | None = None


__all__ = [
    "CoreConnectorsAccess",
    "AccessStatus",
    "AccessRow",
    "AccessDetail",
    "AccessView",
    "ACCESS_STATUSES",
    "ACCESS_STATUS_DISABLED",
    "ACCESS_STATUS_UNCONFIGURED",
    "ACCESS_STATUS_UNDECRYPTABLE",
    "ACCESS_STATUS_ERROR",
    "ACCESS_STATUS_OK",
]
