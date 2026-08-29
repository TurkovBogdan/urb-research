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


async def search_researches(
    query: str,
    *,
    in_body: bool = True,
    in_areas_and_notes: bool = True,
    in_sources: bool = False,
) -> list[str]:
    """Коды исследований, у которых запрос нашёлся в их тексте.

    Стог складывается из слоёв, и каждый включается сам по себе. Название с описанием — основа:
    они и есть то, чем исследование названо в списке, поэтому выключить их нельзя, иначе поиск
    перестал бы находить искомое по имени. Поверх основы ложатся тело исследования
    (``in_body``), написанное внутри него — зоны с брифом и заметки (``in_areas_and_notes``) — и
    материал источников (``in_sources``).

    Источники идут последними и только по не совпавшим: материал на порядок больше всего
    остального (в dev-базе ~29 МБ против сотен килобайт), а исследованию, которое уже совпало
    дешёвым слоем, читать его незачем.

    Группа, сортировка и страница — не наше дело: их накладывает SQL поверх этого списка кодов.
    """
    needle = query.strip().lower()
    written = await _written_texts(in_body=in_body, in_areas_and_notes=in_areas_and_notes)
    matched = [code for code, _group_code, haystack in written if needle in haystack.lower()]
    if not in_sources:
        return matched
    return matched + await _researches_matching_material(needle, skip=set(matched))


async def _researches_matching_material(needle: str, *, skip: set[str]) -> list[str]:
    """Коды исследований, у которых запрос нашёлся в материале их источников."""
    matched: list[str] = []
    for research_code, text in await source_document_crud.source_search_texts():
        if research_code in skip:
            continue
        if needle in text.lower():
            matched.append(research_code)
            skip.add(research_code)
    return matched


async def _written_texts(
    *, in_body: bool, in_areas_and_notes: bool
) -> list[tuple[str, str | None, str]]:
    """``(код, группа, написанный текст исследования одной строкой)`` — корпус обоих поисков.

    Слой, который выключили, не читается вовсе: тело не выбирает колонку в CRUD, а за зонами и
    заметками запросов просто не будет.
    """
    inner_texts: dict[str, list[str]] = {}
    if in_areas_and_notes:
        inner_texts = _texts_by_research(
            await area_crud.area_search_texts() + await note_crud.note_search_texts()
        )
    return [
        (code, group_code, "\n".join([text, *inner_texts.get(code, ())]))
        for code, group_code, text in await research_crud.research_search_texts(
            include_body=in_body
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

    for _code, group_code, haystack in await _written_texts(
        in_body=True, in_areas_and_notes=True
    ):
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
