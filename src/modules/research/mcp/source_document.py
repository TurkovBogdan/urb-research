"""MCP-тулы источников — просмотр + разбор найденных страниц.

Источники не создаются вручную — их находит ``query_search_run``. Тут: список (по уровню
research/area/query, опц. фильтр статуса), деталь (с телом страницы) и разбор одним методом
(``source_review``: решение keep/filter + рейтинг). Ошибка → ``ValueError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import code_prefix, strip_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    DOC_FILTERED,
    DOC_KEPT,
    RESEARCH_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.dto import (
    ResearchSourceDocumentDetail,
    ResearchSourceDocumentRow,
    source_document_detail,
    source_document_row,
)

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP

_DECISION_STATUS = {"keep": DOC_KEPT, "filter": DOC_FILTERED}


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def sources_list(
        code: str, status: str | None = None
    ) -> list[ResearchSourceDocumentRow]:
        """List sources under a research / area / query, in search-launch order.

        The level is taken from the code prefix (RESEARCH@ / AREA@ / QUERY@); url/title come
        joined from the page. Sources are found by query_search_run — there is no manual create.

        Args:
            code: A RESEARCH@ / AREA@ / QUERY@ code — sources of that level.
            status: Optional filter — pending / kept / filtered / fetch_error.
        """
        prefix = code_prefix(code)
        bare = strip_prefix(code)
        if prefix == SOURCE_QUERY_CODE_PREFIX:
            rows = await source_document_crud.source_document_list_by_query(bare, status=status)
        elif prefix == AREA_CODE_PREFIX:
            rows = await source_document_crud.source_document_list_by_area(bare, status=status)
        elif prefix == RESEARCH_CODE_PREFIX:
            rows = await source_document_crud.source_document_list_by_research(bare, status=status)
        else:
            raise ValueError("code must be a RESEARCH@ / AREA@ / QUERY@ code.")
        return [source_document_row(doc, page) for doc, page in rows]

    @mcp.tool()
    async def source_get(source_code: str) -> ResearchSourceDocumentDetail:
        """Return one source — assessment + url/title/body (joined from the page).

        Args:
            source_code: The source code (from sources_list / query_search_run).
        """
        source_code = strip_prefix(source_code)
        result = await source_document_crud.source_document_get(source_code)
        if result is None:
            raise ValueError(f"Source {source_code} not found.")
        doc, page = result
        return source_document_detail(doc, page)

    @mcp.tool()
    async def source_review(
        source_code: str, decision: str, relevance: int, note: str | None = None
    ) -> ResearchSourceDocumentRow:
        """Review a source in one call — decision + rating. Sets the source's status.

        Every source starts `pending` and must be reviewed; review them all before writing the
        area/research synthesis. A `keep` source is one you will cite in a body as SOURCE@<code>.

        Args:
            source_code: The source to review.
            decision: `keep` (goes into the synthesis, cite it as SOURCE@<code>) or `filter`
                (rejected — give a reason in note).
            relevance: Importance 1–10 (1 = junk, 5 = medium/duplicate, 10 = key).
            note: Reason / usefulness — mainly for a filtered source.
        """
        source_code = strip_prefix(source_code)
        status = _DECISION_STATUS.get(decision)
        if status is None:
            raise ValueError("decision must be 'keep' or 'filter'.")
        if not 1 <= relevance <= 10:
            raise ValueError("relevance must be between 1 and 10.")
        row = await source_document_crud.source_document_review(
            source_code, status=status, relevance=relevance, note=note
        )
        if row is None:
            raise ValueError(f"Source {source_code} not found.")
        return source_document_row(row, None)
