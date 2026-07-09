"""MCP-тулы областей исследования — направления/разделы внутри исследования.

Тонкий адаптер над CRUD. Слои области: скан (title/description) для навигации по списку +
бриф-колонки (objective/scope/expectations — цель/границы/формат результата) + результат
(body, синтез раздела). title/description/brief режутся усечением в CRUD (кириллица-safe),
не ошибкой. Ошибка → ``ValueError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import strip_prefix
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.dto import AreaCreated, AreaDetail, AreaRow

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def area_create(
        research_code: str,
        title: str,
        description: str | None = None,
        objective: str | None = None,
        scope: str | None = None,
        expectations: str | None = None,
    ) -> AreaCreated:
        """Add a research area (a thematic direction / report section) under a research.

        An area is the mid level: research → area → query. title/description are the scan
        layer; the brief (objective/scope/expectations) is stored in its own fields and
        decided before you research the area; body (written later) is the section synthesis.
        Overlong fields are trimmed (no error on overflow).

        Args:
            research_code: The research this area belongs to.
            title: Short area name (≤128 chars).
            description: One-line "what this area is" for scanning the list (≤512).
            objective: What to achieve in this area and why (≤1024).
            scope: The boundaries — what is covered and what is explicitly excluded (≤1024).
            expectations: The expected form of the result (≤1024).
        """
        research_code = strip_prefix(research_code)
        if await research_crud.research_get(research_code) is None:
            raise ValueError(f"Research {research_code} not found.")
        row = await area_crud.area_create(
            research_code=research_code,
            title=title,
            description=description,
            objective=objective,
            scope=scope,
            expectations=expectations,
        )
        return AreaCreated.model_validate(row)

    @mcp.tool()
    async def areas_list(research_code: str) -> list[AreaRow]:
        """List a research's areas (scan layer: code, title, description), oldest first.

        Args:
            research_code: The research whose areas to return.
        """
        research_code = strip_prefix(research_code)
        if await research_crud.research_get(research_code) is None:
            raise ValueError(f"Research {research_code} not found.")
        rows = await area_crud.area_list_by_research(research_code)
        return [AreaRow.model_validate(r) for r in rows]

    @mcp.tool()
    async def area_get(area_code: str) -> AreaDetail:
        """Return one area in full — scan layer (title/description) + body.

        Args:
            area_code: The area code returned by area_create.
        """
        area_code = strip_prefix(area_code)
        row = await area_crud.area_get(area_code)
        if row is None:
            raise ValueError(f"Area {area_code} not found.")
        return AreaDetail.model_validate(row)

    @mcp.tool()
    async def area_update(
        area_code: str,
        title: str | None = None,
        description: str | None = None,
        objective: str | None = None,
        scope: str | None = None,
        expectations: str | None = None,
        body: str | None = None,
    ) -> AreaRow:
        """Update an area's fields (omit a field to keep it). Write the section synthesis into body.

        title/description/brief are trimmed to their limits; body is unlimited markdown.

        Args:
            area_code: The area to update.
            title: New title (≤128), or omit to keep.
            description: New one-line description (≤512), or omit.
            objective: New objective (≤1024), or omit.
            scope: New scope / boundaries (≤1024), or omit.
            expectations: New expected form of the result (≤1024), or omit.
            body: New section synthesis in markdown (unlimited), or omit.
        """
        area_code = strip_prefix(area_code)
        row = await area_crud.area_update(
            area_code,
            title=title,
            description=description,
            objective=objective,
            scope=scope,
            expectations=expectations,
            body=body,
        )
        if row is None:
            raise ValueError(f"Area {area_code} not found.")
        return AreaRow.model_validate(row)

    @mcp.tool()
    async def area_delete(area_code: str) -> bool:
        """Delete an area. Returns true if it existed.

        CASCADE: also removes the area's searches and sources.

        Args:
            area_code: The area to delete.
        """
        return await area_crud.area_delete(strip_prefix(area_code))
