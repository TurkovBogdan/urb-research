"""CRUD переноса: полные строки таблиц research для архива и приём чужих строк обратно.

Остальной CRUD модуля отвечает на вопросы предметной области («области исследования», «источники
области»), и его функции отдают ровно то, что нужно экрану. Переносу нужно другое — **строка
целиком, как она лежит**, с кодом, временами и телом, и класть её обратно тоже целиком.

Функции здесь принимают модель параметром, а не заводят по копии на каждую из шести таблиц:
перенос обращается со всеми таблицами одинаково (строка по коду, строка по родителю, вставка
пачкой), и шесть одинаковых тел разъехались бы на первой же правке.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import DatabaseError

from src.core.database import session_scope, write_scope
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery


async def rows_by_codes(model: Any, codes: list[str]) -> dict[str, Any]:
    """``код → строка`` для тех кодов, что уже заняты в этой базе."""
    if not codes:
        return {}
    async with session_scope() as s:
        rows = (await s.execute(select(model).where(model.code.in_(codes)))).scalars().all()
    return {row.code: row for row in rows}


async def codes_in_use(model: Any, codes: list[str]) -> set[str]:
    """Какие из кодов заняты — без вытаскивания самих строк (проверка подменных кодов)."""
    if not codes:
        return set()
    async with session_scope() as s:
        rows = await s.execute(select(model.code).where(model.code.in_(codes)))
        return {code for (code,) in rows.all()}


async def research_row(code: str) -> Research | None:
    async with session_scope() as s:
        return (
            await s.execute(select(Research).where(Research.code == code))
        ).scalar_one_or_none()


async def group_row(code: str) -> ResearchGroup | None:
    async with session_scope() as s:
        return (
            await s.execute(select(ResearchGroup).where(ResearchGroup.code == code))
        ).scalar_one_or_none()


async def rows_by_research(model: Any, research_code: str) -> list[Any]:
    """Строки дочерней таблицы одного исследования, в порядке появления."""
    stmt = (
        select(model)
        .where(model.research_code == research_code)
        .order_by(model.created_at, model.code)
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def source_queries_by_areas(area_codes: list[str]) -> list[ResearchSourceQuery]:
    """Источниковые запросы перечисленных областей — для сверки по естественному ключу."""
    if not area_codes:
        return []
    stmt = select(ResearchSourceQuery).where(ResearchSourceQuery.area_code.in_(area_codes))
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def source_documents_by_queries(query_codes: list[str]) -> list[ResearchSourceDocument]:
    """Источники перечисленных запросов — для сверки по естественному ключу."""
    if not query_codes:
        return []
    stmt = select(ResearchSourceDocument).where(
        ResearchSourceDocument.query_code.in_(query_codes)
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def insert_rows(model: Any, rows: list[dict[str, Any]]) -> int:
    """Вставить строки как есть; занятый код пропускается молча (повторный заход импорта)."""
    if not rows:
        return 0
    async with write_scope() as s:
        dialect = s.bind.dialect.name if s.bind else "postgresql"
        insert = sqlite_insert if dialect == "sqlite" else pg_insert
        await s.execute(
            insert(model).values(rows).on_conflict_do_nothing(index_elements=["code"])
        )
    return len(rows)


async def replace_row(model: Any, code: str, values: dict[str, Any]) -> None:
    """Переписать поля строки значениями из архива (код не трогаем)."""
    if not values:
        return
    async with write_scope() as s:
        await s.execute(update(model).where(model.code == code).values(**values))


async def alembic_heads() -> list[str]:
    """Головы цепочки миграций этой базы — диагностическая отметка в манифесте.

    Таблица читается напрямую: поднимать alembic ради строки в манифесте незачем, а у тестовой
    базы в памяти (схема из ``create_all``) этой таблицы нет вовсе — тогда список пуст.
    """
    try:
        async with session_scope() as s:
            rows = await s.execute(text("SELECT version_num FROM alembic_version"))
            return sorted(version for (version,) in rows.all())
    except DatabaseError:
        return []


__all__ = [
    "alembic_heads",
    "codes_in_use",
    "group_row",
    "insert_rows",
    "replace_row",
    "research_row",
    "rows_by_codes",
    "rows_by_research",
    "source_documents_by_queries",
    "source_queries_by_areas",
]
