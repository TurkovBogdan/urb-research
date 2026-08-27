"""Поиск по написанному тексту: вглубь одного исследования и вширь по всему реестру.

``search_bodies`` — то, чего нет у фронта на странице исследования; ``search_groups`` и
``search_researches`` — поиск по реестру, отвечающий на одном уровне группами, на другом
исследованиями. Общее у них одно, зато главное: сверка идёт по телам и средствами Python
(см. ниже), поэтому все три живут здесь, а не в CRUD.

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
from src.modules.research.crud import group as group_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
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


@dataclass(slots=True)
class GroupMatches:
    """Группы, в которых запрос нашёлся, — плюс признак, что нашлось у неразложенного.

    Псевдо-группа «Без группы» не строка в БД, поэтому кодом её не назвать: она отдельным флагом.
    """

    codes: list[str] = field(default_factory=list)
    ungrouped: bool = False


async def search_researches(query: str, *, in_bodies: bool = True) -> list[str]:
    """Коды исследований, у которых запрос нашёлся в их тексте.

    Тот же корпус, что и у поиска по группам, только ответ на уровень ниже: само исследование,
    его зоны (включая бриф) и заметки; источники не смотрим. Группа, сортировка и страница —
    не наше дело: их накладывает SQL поверх этого списка кодов.

    ``in_bodies=False`` оставляет от корпуса подписи — название и описание исследования; всё
    написанное внутри (его тело, зоны, заметки) из стога выпадает.
    """
    needle = query.strip().lower()
    written = await _written_texts(in_bodies=in_bodies)
    return [code for code, _group_code, haystack in written if needle in haystack.lower()]


async def _written_texts(*, in_bodies: bool) -> list[tuple[str, str | None, str]]:
    """``(код, группа, весь текст исследования одной строкой)`` — общий корпус обоих поисков.

    С выключенными телами написанное внутри исследования не читается вовсе: ни его тело
    (колонку не выбирает CRUD), ни зоны с заметками — запросов за ними просто не будет.
    """
    area_texts = _texts_by_research(await area_crud.area_search_texts()) if in_bodies else {}
    note_texts = _texts_by_research(await note_crud.note_search_texts()) if in_bodies else {}
    return [
        (code, group_code, "\n".join([text, *area_texts.get(code, ()), *note_texts.get(code, ())]))
        for code, group_code, text in await research_crud.research_search_texts(
            include_body=in_bodies
        )
    ]


def _texts_by_research(rows: list[tuple[str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for research_code, text in rows:
        grouped.setdefault(research_code, []).append(text)
    return grouped


async def search_groups(query: str, *, in_researches: bool = True) -> GroupMatches:
    """Какие группы оставить на странице реестра при запросе ``query``.

    Группа совпадает, если запрос нашёлся в её собственном тексте **или** в тексте любого
    входящего в неё исследования — считая тела его зон и заметок. Источники не смотрим: их
    материал скачан извне, а не написан здесь, и по объёму он на два порядка больше всего
    остального.

    Порог длины запроса (``MIN_QUERY_LENGTH``) тут не применяется, и это осознанно: там он бережёт
    от чтения мегабайтов материала ради мусорного ответа, а здесь корпус без источников и ответ —
    фильтр, где «совпало всё» и «ничего не набрано» обязаны выглядеть одинаково. Пустой запрос
    поэтому и означает «не сужать».

    ``in_researches=False`` оставляет от корпуса собственный текст групп: что в группе лежит, не
    смотрим вовсе. Псевдо-группа «Без группы» при этом не совпадает никогда — своего текста у неё
    нет, она и есть остаток.
    """
    needle = query.strip().lower()
    groups = await group_crud.group_search_texts()
    if not needle:
        return GroupMatches(codes=[code for code, _ in groups], ungrouped=True)

    matched = {code for code, text in groups if needle in text.lower()}
    ungrouped = False
    if not in_researches:
        return GroupMatches(codes=sorted(matched), ungrouped=ungrouped)

    for _code, group_code, haystack in await _written_texts(in_bodies=True):
        if needle not in haystack.lower():
            continue
        if group_code is None:
            ungrouped = True
        else:
            matched.add(group_code)

    return GroupMatches(codes=sorted(matched), ungrouped=ungrouped)


__all__ = [
    "DeepMatches",
    "GroupMatches",
    "MIN_QUERY_LENGTH",
    "search_bodies",
    "search_groups",
    "search_researches",
]
