"""CRUD ``Research`` — исследования. Каждая функция владеет сессией.

Read'ы, которым нужно имя полки, джойнят ``research_group`` по ``group_code`` и возвращают
кортежи ``(research, group|None)`` — ``group`` пустая, пока исследование не разложено. Название
группы нигде не копируется: у исследования хранится только ссылка.
"""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.sql.selectable import Select

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.constants import DOC_FILTERED, DOC_KEPT
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery

ResearchWithGroup = tuple[Research, ResearchGroup | None]

def research_code() -> str:
    """Код исследования — голый 22-hex ``random_hash`` (дедупа по заголовку нет, каждый свой).

    Тип-префикс (``RESEARCH@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


def _filtered(stmt: Select, *, query: str | None, group_code: str | None = None) -> Select:
    """Фильтры списка: подстрока заголовка + полка.

    ``group_code``: ``None`` — не фильтровать, ``""`` — только неразложенные (единственная форма
    спросить про ``NULL``), код — только эта полка. Та же тройка значений, что у ``research_update``.
    """
    if query:
        stmt = stmt.where(Research.title.ilike(f"%{query}%"))
    if group_code == "":
        stmt = stmt.where(Research.group_code.is_(None))
    elif group_code is not None:
        stmt = stmt.where(Research.group_code == group_code)
    return stmt


def _with_group():
    """Исследование + его полка; outer join — неразложенные строки остаются в выборке."""
    return select(Research, ResearchGroup).outerjoin(
        ResearchGroup, Research.group_code == ResearchGroup.code
    )


def _children_count(model, *conditions):
    """Скалярный подзапрос «сколько дочерних строк у этого исследования».

    Коррелирует по ``research_code`` с внешним ``Research``, поэтому годится прямо в ``ORDER BY``
    списка — счётчики на карточке считаются отдельными GROUP BY (по кодам страницы), но
    сортировать по ним можно только в SQL.
    """
    return (
        select(func.count())
        .select_from(model)
        .where(model.research_code == Research.code, *conditions)
        .scalar_subquery()
    )


# По чему разрешено сортировать список (белый список = защита от инъекции: неизвестный ключ
# падает в дефолт). Совпадает с колонками таблицы реестра плюс дата создания.
RESEARCH_SORT_COLUMNS = {
    "created_at": Research.created_at,
    "updated_at": Research.updated_at,
    "title": Research.title,
    "area_count": _children_count(ResearchArea),
    "query_count": _children_count(ResearchSourceQuery),
    "document_kept": _children_count(
        ResearchSourceDocument, ResearchSourceDocument.status == DOC_KEPT
    ),
    "document_filtered": _children_count(
        ResearchSourceDocument, ResearchSourceDocument.status == DOC_FILTERED
    ),
}
RESEARCH_SORT_DEFAULT = "created_at"


async def research_list_paged(
    *,
    query: str | None,
    sort_by: str = RESEARCH_SORT_DEFAULT,
    sort_dir: str,
    offset: int,
    limit: int,
    group_code: str | None = None,
) -> list[ResearchWithGroup]:
    """Страница списка. Сортировка — по ключу из ``RESEARCH_SORT_COLUMNS`` (неизвестный →
    ``created_at``); ``code`` — стабильный тайбрейк в ту же сторону."""
    column = RESEARCH_SORT_COLUMNS.get(sort_by, Research.created_at)
    ascending = sort_dir == "asc"
    order = (column.asc(), Research.code.asc()) if ascending else (column.desc(), Research.code.desc())
    stmt = _filtered(_with_group(), query=query, group_code=group_code).order_by(
        *order
    ).offset(offset).limit(limit)
    async with session_scope() as s:
        rows = (await s.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def research_count(*, query: str | None, group_code: str | None = None) -> int:
    stmt = _filtered(
        select(func.count()).select_from(Research), query=query, group_code=group_code
    )
    async with session_scope() as s:
        return int((await s.execute(stmt)).scalar_one())


async def research_create(
    *,
    title: str,
    description: str | None = None,
    body: str | None = None,
    group_code: str | None = None,
) -> Research:
    async with session_scope() as s:
        row = Research(
            code=research_code(),
            group_code=group_code or None,
            title=title,
            description=description or "",
            body=body or "",
        )
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


async def research_get(code: str) -> Research | None:
    async with session_scope() as s:
        return await s.get(Research, code)


async def research_get_with_group(code: str) -> ResearchWithGroup | None:
    stmt = _with_group().where(Research.code == code)
    async with session_scope() as s:
        row = (await s.execute(stmt)).first()
    return (row[0], row[1]) if row else None


async def research_list_with_group(
    *, group_code: str | None = None
) -> list[ResearchWithGroup]:
    stmt = _filtered(_with_group(), query=None, group_code=group_code).order_by(
        Research.updated_at.desc(), Research.code.desc()
    )
    async with session_scope() as s:
        rows = (await s.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def research_update(
    code: str,
    *,
    title: str | None = None,
    description: str | None = None,
    body: str | None = None,
    group_code: str | None = None,
) -> Research | None:
    """Обновить переданные поля исследования (``None`` = не трогать).

    ``group_code=""`` — снять с полки (``NULL``): пустая строка означает «не задано» во всех
    текстовых полях модуля, а для ссылки единственная форма «не задано» — ``NULL``.
    """
    async with session_scope() as s:
        row = await s.get(Research, code)
        if row is None:
            return None
        if title is not None:
            row.title = title
        if description is not None:
            row.description = description
        if body is not None:
            row.body = body
        if group_code is not None:
            row.group_code = group_code or None
        await s.flush()
        await s.refresh(row)
    return row


async def research_count_by_group_codes(group_codes: list[str]) -> dict[str, int]:
    """``group_code → число исследований`` одним GROUP BY (для списка полок)."""
    if not group_codes:
        return {}
    stmt = (
        select(Research.group_code, func.count())
        .where(Research.group_code.in_(group_codes))
        .group_by(Research.group_code)
    )
    async with session_scope() as s:
        return {code: count for code, count in (await s.execute(stmt)).all()}


async def research_delete(code: str) -> bool:
    """Удалить исследование целиком. Каскад — вручную (sqlite FK-каскад выключен): источники →
    запросы → заметки → области → само исследование. ``True`` — существовало и удалено."""
    async with session_scope() as s:
        row = await s.get(Research, code)
        if row is None:
            return False
        for model in (
            ResearchSourceDocument,
            ResearchSourceQuery,
            ResearchNote,
            ResearchArea,
        ):
            await s.execute(delete(model).where(model.research_code == code))
        await s.delete(row)
    return True


__all__ = [
    "RESEARCH_SORT_COLUMNS",
    "RESEARCH_SORT_DEFAULT",
    "research_code",
    "research_list_paged",
    "research_count",
    "research_create",
    "research_get",
    "research_get_with_group",
    "research_list_with_group",
    "research_update",
    "research_count_by_group_codes",
    "research_delete",
]
