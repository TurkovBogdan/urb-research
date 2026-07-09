"""CRUD ``ResearchNote`` — типизированные заметки исследования. Сессия на функцию.

Заметка = мини-артефакт рабочей памяти: обязательный ``kind`` + типовые поля описания
(title/description/body). ``title``/``description`` усекаются по **code points** (кириллица-safe,
как у области), ``body`` без лимита. Валидность ``kind`` держит ``CHECK`` в БД; MCP отклоняет
неизвестный тип до вставки (внятная ошибка).
"""

from __future__ import annotations

from sqlalchemy import select

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.constants import NOTE_DESCRIPTION_MAX, NOTE_TITLE_MAX
from src.modules.research.models.note import ResearchNote

def note_code() -> str:
    """Код заметки — голый 22-hex ``random_hash``.

    Тип-префикс (``NOTE@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


def _clip(value: str | None, limit: int) -> str:
    """Усечь строку до ``limit`` символов Unicode; ``None`` → ``""`` (поле не nullable)."""
    return (value or "")[:limit]


async def note_create(
    *,
    research_code: str,
    kind: str,
    title: str,
    description: str | None = None,
    body: str | None = None,
) -> ResearchNote:
    async with session_scope() as s:
        row = ResearchNote(
            code=note_code(),
            research_code=research_code,
            kind=kind,
            title=_clip(title, NOTE_TITLE_MAX),
            description=_clip(description, NOTE_DESCRIPTION_MAX),
            body=body or "",
        )
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


async def note_get(code: str) -> ResearchNote | None:
    async with session_scope() as s:
        return await s.get(ResearchNote, code)


async def note_list_by_research(
    research_code: str, *, kind: str | None = None
) -> list[ResearchNote]:
    stmt = select(ResearchNote).where(ResearchNote.research_code == research_code)
    if kind is not None:
        stmt = stmt.where(ResearchNote.kind == kind)
    stmt = stmt.order_by(ResearchNote.created_at.asc(), ResearchNote.code.asc())
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def note_update(
    code: str,
    *,
    kind: str | None = None,
    title: str | None = None,
    description: str | None = None,
    body: str | None = None,
) -> ResearchNote | None:
    """Обновить переданные поля заметки (``None`` = не трогать; ``body`` без лимита)."""
    async with session_scope() as s:
        row = await s.get(ResearchNote, code)
        if row is None:
            return None
        if kind is not None:
            row.kind = kind
        if title is not None:
            row.title = _clip(title, NOTE_TITLE_MAX)
        if description is not None:
            row.description = _clip(description, NOTE_DESCRIPTION_MAX)
        if body is not None:
            row.body = body
        await s.flush()
        await s.refresh(row)
    return row


async def note_delete(code: str) -> bool:
    """Удалить заметку. ``True`` — существовала и удалена."""
    async with session_scope() as s:
        row = await s.get(ResearchNote, code)
        if row is None:
            return False
        await s.delete(row)
    return True


__all__ = [
    "note_code",
    "note_create",
    "note_get",
    "note_list_by_research",
    "note_update",
    "note_delete",
]
