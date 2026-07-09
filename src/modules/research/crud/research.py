"""CRUD ``Research`` — исследования. Каждая функция владеет сессией."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.sql.selectable import Select

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery

def research_code() -> str:
    """Код исследования — голый 22-hex ``random_hash`` (дедупа по заголовку нет, каждый свой).

    Тип-префикс (``RESEARCH@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


def _filtered(stmt: Select, *, query: str | None) -> Select:
    if query:
        stmt = stmt.where(Research.title.ilike(f"%{query}%"))
    return stmt


async def research_list_paged(
    *,
    query: str | None,
    sort_dir: str,
    offset: int,
    limit: int,
) -> list[Research]:
    order = Research.created_at.asc() if sort_dir == "asc" else Research.created_at.desc()
    tiebreak = Research.code.asc() if sort_dir == "asc" else Research.code.desc()
    stmt = _filtered(select(Research), query=query).order_by(
        order, tiebreak
    ).offset(offset).limit(limit)
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def research_count(*, query: str | None) -> int:
    stmt = _filtered(select(func.count()).select_from(Research), query=query)
    async with session_scope() as s:
        return int((await s.execute(stmt)).scalar_one())


async def research_create(
    *, title: str, description: str | None = None, body: str | None = None
) -> Research:
    async with session_scope() as s:
        row = Research(
            code=research_code(),
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


async def research_list() -> list[Research]:
    stmt = select(Research).order_by(Research.updated_at.desc(), Research.code.desc())
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def research_update(
    code: str,
    *,
    title: str | None = None,
    description: str | None = None,
    body: str | None = None,
) -> Research | None:
    """Обновить переданные поля исследования (``None`` = не трогать)."""
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
        await s.flush()
        await s.refresh(row)
    return row


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
    "research_code",
    "research_list_paged",
    "research_count",
    "research_create",
    "research_get",
    "research_list",
    "research_update",
    "research_delete",
]
