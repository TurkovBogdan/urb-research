"""Паспорт коннектора и результаты его двух обязанностей — баланса и проверки.

Паспорт (``ConnectorPassport``) — то, что коннектор объявляет о себе кодом: код сервиса,
имя, описание, модуль-владелец регистрации, умеет ли баланс и из каких полей состоит
доступ. Дескрипторы полей строятся ядровыми ``Field.ui_descriptor()`` — второй системы
полей в проекте нет; ``is_set`` дописывается по конкретной записи доступа (секрет наружу
не уходит, наружу идёт лишь факт «задан»).

``ConnectorBalance``/``BalanceMetric`` — остаток как **список метрик**: у коннектора может
быть несколько независимых показателей (фактический баланс, лимит ключа, расход за окно).
Каждая метрика сама выбирает форму — денежную (``amount``+``currency``) либо «использовано
из всего» (``used``/``total``+``used_percent``+``unit``). ``ConnectorCheck`` — результат
живой проверки доступа.

Модуль чистый (без внутренних импортов, кроме ядровых полей) — на него опираются база,
коннекторы и реестр без циклов.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from src.core.settings import Field


class ConnectorPassport(BaseModel):
    service: str  # код коннектора в реестре: tavily | firecrawl | xai …
    name: str
    description: str
    group: str  # код группы справочника; пусто — «Прочее»
    owner: str  # модуль, зарегистрировавший коннектор
    has_balance: bool
    fields: list[dict[str, Any]]  # дескрипторы полей доступа (ядровый ui_descriptor)


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


class ConnectorCheck(BaseModel):
    """Результат живой проверки доступа: дошли ли до сервиса и за сколько."""

    ok: bool
    latency_ms: int | None = None
    error: str | None = None


def field_descriptors(
    fields: tuple[Field, ...], *, is_set: frozenset[str] | None = None
) -> list[dict[str, Any]]:
    """Дескрипторы полей паспорта для формы.

    ``is_set`` — ключи секретов, у которых в записи есть значение; признак дописывается
    только когда запись известна (у паспорта самого по себе заполненности нет). Само
    значение сюда не попадает никогда: наружу уходит лишь факт заполненности.
    """
    descriptors = []
    for field in fields:
        descriptor = field.ui_descriptor()
        if is_set is not None and field.is_secret():
            descriptor["is_set"] = field.key in is_set
        descriptors.append(descriptor)
    return descriptors


__all__ = [
    "ConnectorPassport",
    "BalanceMetric",
    "ConnectorBalance",
    "ConnectorCheck",
    "field_descriptors",
]
