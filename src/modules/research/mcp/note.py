"""MCP-тулы заметок исследования — типизированная рабочая память.

Тонкий адаптер над CRUD. Заметка — самостоятельный мини-артефакт (title/description/body)
с обязательным типом (``kind``), фиксирующий то, что не привязано к документу или разделу:
вывод / гипотезу / вопрос / наблюдение / решение. Тип заставляет агента классифицировать
(«схема как промпт»); неизвестный тип и отсутствие сущностей → ``ValueError``. title/description
режутся усечением в CRUD (кириллица-safe), не ошибкой.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import strip_prefix
from src.modules.research.constants import NOTE_KINDS, sql_in
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.dto import NoteCreated, NoteDetail, NoteRow

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def _require_kind(kind: str) -> None:
    if kind not in NOTE_KINDS:
        raise ValueError(f"Unknown note kind {kind!r}. Allowed: {sql_in(NOTE_KINDS)}.")


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def note_create(
        research_code: str,
        kind: str,
        title: str,
        description: str | None = None,
        body: str | None = None,
    ) -> NoteCreated:
        """Add a typed working-memory note to a research (a self-contained mini-artifact).

        A note captures what does not belong to a single document or area — a finding, a
        hypothesis, an open question, a raw observation or a methodological decision. The kind
        is required: it forces you to classify what you are recording.

        Kinds: `result` (an established finding/conclusion, a synthesis candidate), `idea` (a
        hypothesis / direction to dig into), `question` (an open gap, what is still unclear),
        `memory` (a raw observation / context to keep between sessions), `decision` (a choice
        made along the way — methodology, what was included/excluded — so it is not re-litigated),
        `clarification` (a clarification or constraint the user gave that steers or narrows the
        research — scope, priorities, definitions; use this for what the user told you, as opposed
        to `decision` which is your own methodological choice).

        Args:
            research_code: The research this note belongs to.
            kind: One of result / idea / question / memory / decision / clarification.
            title: Short note name (≤128 chars).
            description: One-line "what this is" for scanning the list (≤512).
            body: The note itself in markdown (unlimited), or omit.
        """
        _require_kind(kind)
        research_code = strip_prefix(research_code)
        if await research_crud.research_get(research_code) is None:
            raise ValueError(f"Research {research_code} not found.")
        row = await note_crud.note_create(
            research_code=research_code,
            kind=kind,
            title=title,
            description=description,
            body=body,
        )
        return NoteCreated.model_validate(row)

    @mcp.tool()
    async def notes_list(research_code: str, kind: str | None = None) -> list[NoteRow]:
        """List a research's notes (scan layer: code, kind, title, description), oldest first.

        Args:
            research_code: The research whose notes to return.
            kind: Optional filter — result / idea / question / memory / decision / clarification.
        """
        research_code = strip_prefix(research_code)
        if kind is not None:
            _require_kind(kind)
        if await research_crud.research_get(research_code) is None:
            raise ValueError(f"Research {research_code} not found.")
        rows = await note_crud.note_list_by_research(research_code, kind=kind)
        return [NoteRow.model_validate(r) for r in rows]

    @mcp.tool()
    async def note_get(note_code: str) -> NoteDetail:
        """Return one note in full — scan layer + body.

        Args:
            note_code: The note code returned by note_create.
        """
        note_code = strip_prefix(note_code)
        row = await note_crud.note_get(note_code)
        if row is None:
            raise ValueError(f"Note {note_code} not found.")
        return NoteDetail.model_validate(row)

    @mcp.tool()
    async def note_update(
        note_code: str,
        kind: str | None = None,
        title: str | None = None,
        description: str | None = None,
        body: str | None = None,
    ) -> NoteRow:
        """Update a note's fields (omit a field to keep it).

        title/description are trimmed to their limits; body is unlimited markdown.

        Args:
            note_code: The note to update.
            kind: New kind (result/idea/question/memory/decision/clarification), or omit to keep.
            title: New title (≤128), or omit.
            description: New one-line description (≤512), or omit.
            body: New body in markdown (unlimited), or omit.
        """
        note_code = strip_prefix(note_code)
        if kind is not None:
            _require_kind(kind)
        row = await note_crud.note_update(
            note_code, kind=kind, title=title, description=description, body=body
        )
        if row is None:
            raise ValueError(f"Note {note_code} not found.")
        return NoteRow.model_validate(row)

    @mcp.tool()
    async def note_delete(note_code: str) -> bool:
        """Delete a note. Returns true if it existed and was removed.

        Args:
            note_code: The note to delete.
        """
        return await note_crud.note_delete(strip_prefix(note_code))
