"""CRUD ``ResearchArea`` — области исследования. Каждая функция владеет сессией.

Размеры полей — **не** ошибка валидации, а мягкое усечение здесь, в CRUD: ``_clip``
режет по **code points** (``value[:limit]`` на ``str`` считает символы Unicode, не байты),
поэтому кириллица и прочий многобайтовый Unicode не рубятся посреди символа. Это
совпадает с символьной семантикой ``VARCHAR(n)`` в PostgreSQL; SQLite длину не проверяет
вовсе — здесь усечение и есть единственная реальная граница. ``body`` без лимита — не режем.
"""

from __future__ import annotations

from sqlalchemy import delete, func, select

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.constants import (
    AREA_BRIEF_MAX,
    AREA_DESCRIPTION_MAX,
    AREA_TITLE_MAX,
)
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery

def area_code() -> str:
    """Код области — голый 22-hex ``random_hash`` (естественного ключа дедупа нет).

    Тип-префикс (``AREA@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


def _clip(value: str | None, limit: int) -> str:
    """Усечь строку до ``limit`` символов Unicode; ``None`` → ``""`` (поле не nullable)."""
    return (value or "")[:limit]


async def area_create(
    *,
    research_code: str,
    title: str,
    description: str | None = None,
    objective: str | None = None,
    scope: str | None = None,
    expectations: str | None = None,
) -> ResearchArea:
    async with session_scope() as s:
        row = ResearchArea(
            code=area_code(),
            research_code=research_code,
            title=_clip(title, AREA_TITLE_MAX),
            description=_clip(description, AREA_DESCRIPTION_MAX),
            objective=_clip(objective, AREA_BRIEF_MAX),
            scope=_clip(scope, AREA_BRIEF_MAX),
            expectations=_clip(expectations, AREA_BRIEF_MAX),
        )
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


async def area_get(code: str) -> ResearchArea | None:
    async with session_scope() as s:
        return await s.get(ResearchArea, code)


async def area_list_by_research(research_code: str) -> list[ResearchArea]:
    stmt = (
        select(ResearchArea)
        .where(ResearchArea.research_code == research_code)
        .order_by(
            ResearchArea.created_at.asc(),
            ResearchArea.code.asc(),
        )
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def area_update(
    code: str,
    *,
    title: str | None = None,
    description: str | None = None,
    objective: str | None = None,
    scope: str | None = None,
    expectations: str | None = None,
    body: str | None = None,
) -> ResearchArea | None:
    """Обновить переданные поля области (``None`` = не трогать; ``body`` без лимита)."""
    async with session_scope() as s:
        row = await s.get(ResearchArea, code)
        if row is None:
            return None
        if title is not None:
            row.title = _clip(title, AREA_TITLE_MAX)
        if description is not None:
            row.description = _clip(description, AREA_DESCRIPTION_MAX)
        if objective is not None:
            row.objective = _clip(objective, AREA_BRIEF_MAX)
        if scope is not None:
            row.scope = _clip(scope, AREA_BRIEF_MAX)
        if expectations is not None:
            row.expectations = _clip(expectations, AREA_BRIEF_MAX)
        if body is not None:
            row.body = body
        await s.flush()
        await s.refresh(row)
    return row


async def area_delete(code: str) -> bool:
    """Удалить область. Каскад вручную: источники → запросы области → сама область.
    ``True`` — существовала и удалена."""
    async with session_scope() as s:
        row = await s.get(ResearchArea, code)
        if row is None:
            return False
        for model in (ResearchSourceDocument, ResearchSourceQuery):
            await s.execute(delete(model).where(model.area_code == code))
        await s.delete(row)
    return True


async def area_count_by_research_codes(research_codes: list[str]) -> dict[str, int]:
    """``research_code → число областей`` одним GROUP BY (для списка исследований)."""
    if not research_codes:
        return {}
    stmt = (
        select(ResearchArea.research_code, func.count())
        .where(ResearchArea.research_code.in_(research_codes))
        .group_by(ResearchArea.research_code)
    )
    async with session_scope() as s:
        return {code: count for code, count in (await s.execute(stmt)).all()}


__all__ = [
    "area_code",
    "area_create",
    "area_get",
    "area_list_by_research",
    "area_update",
    "area_delete",
    "area_count_by_research_codes",
]
