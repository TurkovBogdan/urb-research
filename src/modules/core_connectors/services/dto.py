"""DTO коннекторов — общие read-модели: паспорт коннектора и его баланс.

Держим раздельно два DTO (их и получает реестр):
- ``ConnectorInfo`` — паспорт коннектора: код, имя, описание, включён ли, умеет ли баланс;
- ``ConnectorBalance`` — остаток как **список метрик** ``metrics``: у коннектора может быть
  несколько независимых показателей (фактический баланс, лимит по ключу, кредиты — одно
  другое не отменяет). Каждая ``BalanceMetric`` сама решает форму: денежная величина
  (``amount``+``currency``) ИЛИ «использовано из всего» (``used``/``total``+``used_percent``+
  ``unit``). ``error`` — если коннектор включён, но баланс получить не удалось. Показываем
  только те метрики, что сервис реально отдал.
``ConnectorView`` = паспорт + опциональный баланс (см. ``ConnectorsRegistry``).
Модуль чистый (без внутренних импортов) — на него опираются база/гейтвеи/реестр без циклов.
"""

from __future__ import annotations

from pydantic import BaseModel


class ConnectorInfo(BaseModel):
    service: str  # код коннектора: tavily | firecrawl | xai
    name: str
    description: str
    enabled: bool  # не отключён тумблером
    has_balance: bool  # умеет ли отдавать баланс


class BalanceMetric(BaseModel):
    label: str  # человекочитаемое имя показателя: «Баланс» / «Кредиты» / «Лимит ключа»
    amount: float | None = None  # денежная величина (остаток/баланс)
    currency: str | None = None  # для денежной метрики
    used: float | None = None  # для «использовано из всего»
    total: float | None = None
    used_percent: float | None = None  # доля использованного, 0..100
    unit: str | None = None  # credits | tokens | USD …

    @classmethod
    def money(cls, label: str, amount: float | None, *, currency: str = "USD") -> "BalanceMetric":
        return cls(label=label, amount=amount, currency=currency)

    @classmethod
    def usage(
        cls, label: str, *, used: float | None, total: float | None, unit: str
    ) -> "BalanceMetric":
        """Метрика «использовано из всего» — сама считает % использования."""
        percent = round(used / total * 100, 1) if total and used is not None else None
        return cls(label=label, used=used, total=total, used_percent=percent, unit=unit)


class ConnectorBalance(BaseModel):
    service: str
    name: str
    metrics: list[BalanceMetric] = []
    error: str | None = None


class ConnectorView(BaseModel):
    info: ConnectorInfo
    balance: ConnectorBalance | None = None  # заполнен при запросе with_balance


__all__ = ["ConnectorInfo", "BalanceMetric", "ConnectorBalance", "ConnectorView"]
