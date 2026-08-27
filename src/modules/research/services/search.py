"""Глубокий поиск по исследованию — то, чего нет у фронта.

Деталь исследования отдаёт вложенные сущности скан-слоем (название + описание), поэтому мгновенный
поиск на клиенте по телам искать не может: синтез зоны, тело заметки и материал страницы живут за
отдельными ручками, а материал у одного исследования доходит до полутора десятков мегабайт. Эта
служба берёт на себя ровно недостающую половину: возвращает **коды** тех сущностей, у которых
совпало в теле. Клиент объединяет их со своими совпадениями по скан-слою.

**Сверка идёт в Python, а не в SQL,** и это не лень: у SQLite `LIKE` регистронезависим только для
ASCII, а `lower()` кириллицу вообще не трогает (``lower('Ж') == 'Ж'``) — запрос «оренбург» не нашёл
бы «Оренбург». Питоновский ``str.lower`` складывает регистр правильно и одинаково на обоих
провайдерах БД. Цена измерена на самом большом исследовании dev-базы (753 страницы, 15.7 МБ):
99 мс против 35 мс у неверного SQL-варианта.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.research.crud import area as area_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import source_document as source_document_crud

# Однобуквенный запрос совпадает почти со всем и заставляет читать все тела ради мусорного ответа.
MIN_QUERY_LENGTH = 2


@dataclass(slots=True)
class DeepMatches:
    """Коды сущностей, у которых запрос нашёлся **в теле** (не в названии и не в описании)."""

    areas: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def _matching_codes(rows: list[tuple[str, str | None]], needle: str) -> list[str]:
    return [code for code, text in rows if text and needle in text.lower()]


async def search_bodies(research_code: str, query: str) -> DeepMatches:
    """Пройти по телам зон, заметок и материалу источников исследования.

    Короткий запрос — пустой ответ, а не отказ: строку набирают по букве, и первая же из них
    не должна выглядеть как ошибка.
    """
    needle = query.strip().lower()
    if len(needle) < MIN_QUERY_LENGTH:
        return DeepMatches()

    return DeepMatches(
        areas=_matching_codes(await area_crud.area_bodies_by_research(research_code), needle),
        notes=_matching_codes(await note_crud.note_bodies_by_research(research_code), needle),
        sources=_matching_codes(
            await source_document_crud.source_material_by_research(research_code), needle
        ),
    )


__all__ = ["DeepMatches", "MIN_QUERY_LENGTH", "search_bodies"]
