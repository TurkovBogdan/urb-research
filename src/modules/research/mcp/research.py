"""MCP-тулы реестра исследований + поисков источников (source_query).

Тонкий адаптер над CRUD: тул строит форму, зовёт crud, отдаёт DTO. Ошибка →
``ValueError`` (fastmcp превратит в ToolError). ``query_search_run`` — единственный, кто выходит
за CRUD: запускает web_search (блокирующе) и наполняет источники.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import code_prefix, strip_prefix
from src.modules.research.constants import AREA_CODE_PREFIX, RESEARCH_CODE_PREFIX
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.research.dto import (
    AreaScan,
    NoteScan,
    ResearchCreated,
    ResearchListItem,
    ResearchScan,
    ResearchSourceDocumentRow,
    ResearchSourceQueryRow,
    ResearchView,
    source_document_row,
)
from src.modules.web_search.crud import query_result as query_result_crud
from src.modules.web_search.services.searcher import Searcher

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def _oldest_first(rows: list) -> list:
    """Отсортировать области/заметки по ``updated_at`` по возрастанию (старые → новые)."""
    return sorted(rows, key=lambda row: row.updated_at)


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def research_create(
        title: str, description: str | None = None, body: str | None = None
    ) -> ResearchCreated:
        """Start a research (knowledge artifact) and register it. Returns only its code.

        Args:
            title: The research title / name (up to 128 chars).
            description: Optional short description / abstract (up to 512 chars).
            body: Optional main body in markdown (fill in as the research progresses).
        """
        row = await research_crud.research_create(
            title=title, description=description, body=body
        )
        return ResearchCreated.model_validate(row)

    @mcp.tool()
    async def research_get(research_code: str) -> ResearchView:
        """Return one research in full — its fields and body, plus its areas and notes.

        Areas and notes are the scan layer (code, title, description, updated_at),
        ordered by update time oldest first.

        Args:
            research_code: The research code returned by research_create.
        """
        research_code = strip_prefix(research_code)
        row = await research_crud.research_get(research_code)
        if row is None:
            raise ValueError(f"Research {research_code} not found.")
        areas = await area_crud.area_list_by_research(research_code)
        notes = await note_crud.note_list_by_research(research_code)
        return ResearchView(
            code=row.code,
            title=row.title,
            description=row.description,
            body=row.body,
            areas=[AreaScan.model_validate(a) for a in _oldest_first(areas)],
            notes=[NoteScan.model_validate(n) for n in _oldest_first(notes)],
            updated_at=row.updated_at,
        )

    @mcp.tool()
    async def research_list() -> list[ResearchListItem]:
        """List all researches, most recently updated first (code, title, description, updated_at)."""
        rows = await research_crud.research_list()
        return [ResearchListItem.model_validate(r) for r in rows]

    @mcp.tool()
    async def research_update(
        research_code: str,
        title: str | None = None,
        description: str | None = None,
        body: str | None = None,
    ) -> ResearchScan:
        """Update a research's title / description / body (omit a field to keep it).

        Returns the updated scan (code, title, description). For incremental body edits use body_edit.

        Args:
            research_code: The research to update.
            title: New title (up to 128 chars), or omit to keep the current one.
            description: New short description (up to 512 chars), or omit to keep.
            body: New main body in markdown, or omit to keep the current one.
        """
        research_code = strip_prefix(research_code)
        row = await research_crud.research_update(
            research_code, title=title, description=description, body=body
        )
        if row is None:
            raise ValueError(f"Research {research_code} not found.")
        return ResearchScan.model_validate(row)

    @mcp.tool()
    async def research_delete(research_code: str) -> bool:
        """Delete a research entirely. Returns true if it existed.

        CASCADE: also removes all of its areas, notes, searches and sources.

        Args:
            research_code: The research to delete.
        """
        return await research_crud.research_delete(strip_prefix(research_code))

    @mcp.tool()
    async def query_search_run(area_code: str, query: str) -> list[ResearchSourceDocumentRow]:
        """Run a web search for an area and return the sources it found (blocking).

        Runs web_search to completion, records the run as a source-query under the area's
        research, registers each found page as a `pending` source, and returns the source
        list (no body — read one with source_get). Prefer delegating an area's searches to a
        dedicated sub-agent: the call blocks and every returned source must then be reviewed.

        NEXT STEP IS MANDATORY: every source comes back `pending`. Read each with source_get
        and judge it with source_review (keep/filter + relevance) before writing any synthesis —
        a source left `pending` is unfinished work.

        Args:
            area_code: The area to search sources for (its research is taken from the area).
            query: The search query text.
        """
        area_code = strip_prefix(area_code)
        area = await area_crud.area_get(area_code)
        if area is None:
            raise ValueError(f"Area {area_code} not found.")
        run = await Searcher.search(query)
        sq = await source_query_crud.source_query_create(
            research_code=area.research_code,
            area_code=area_code,
            search_code=run.code,
            query=query,
        )
        sources: list[ResearchSourceDocumentRow] = []
        for result, page in await query_result_crud.results_with_page_for_query(run.code):
            doc = await source_document_crud.source_document_create(
                research_code=area.research_code,
                area_code=area_code,
                query_code=sq.code,
                page_code=page.code,
                summary=result.summary,
            )
            sources.append(source_document_row(doc, page))
        return sources

    @mcp.tool()
    async def query_search_list(code: str) -> list[ResearchSourceQueryRow]:
        """List the searches (source-queries) under an area or a research.

        Args:
            code: An AREA@ code (its searches) or a RESEARCH@ code (all its searches).
        """
        prefix = code_prefix(code)
        bare = strip_prefix(code)
        if prefix == AREA_CODE_PREFIX:
            rows = await source_query_crud.source_query_list_by_area(bare)
        elif prefix == RESEARCH_CODE_PREFIX:
            rows = await source_query_crud.source_query_list_by_research(bare)
        else:
            raise ValueError("code must be an AREA@ or RESEARCH@ code.")
        return [ResearchSourceQueryRow.model_validate(r) for r in rows]

    @mcp.tool()
    async def query_search_delete(query_code: str) -> bool:
        """Delete a search run. Returns true if it existed.

        CASCADE: also removes the sources found by that run.

        Args:
            query_code: The search (source-query) to delete.
        """
        return await source_query_crud.source_query_delete(strip_prefix(query_code))
