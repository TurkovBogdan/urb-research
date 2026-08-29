"""MCP-тулы источников — просмотр, повтор получения и разбор найденных страниц.

Источники не создаются вручную — их находит ``query_search_run``. Тут: список (по уровню
research/area/query, опц. фильтр статуса), деталь (с телом страницы), повтор получения контента
(``sources_refetch``: тот же диспетч по уровню плюс одиночный источник, до
``SOURCES_REFETCH_MAX`` кодов за вызов) и разбор одним методом (``source_review``: решение
keep/filter + рейтинг). Ошибка → ``ValueError``.

Бесплодный код в ``sources_refetch`` **не роняет вызов**: у пакета из шести кодов один
промах не должен отменять работу по остальным пяти, поэтому промахи уходят в отчёт
(``skipped``), а исключение остаётся за тем, что ломает вызов целиком, — пустым списком,
перебором потолка и выключенным движком.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import code_prefix, strip_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    DOC_ERROR,
    DOC_FILTERED,
    DOC_KEPT,
    RESEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud.source_document import SourceDocumentWithPage
from src.modules.research.dto import (
    AgentSourceDocumentDetail,
    ResearchSourceDocumentRow,
    AgentSkippedCode,
    AgentSourcesRefetched,
    agent_source_document_detail,
    source_document_row,
)
from src.modules.research.services.refetch import refetch_sources

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP

_DECISION_STATUS = {"keep": DOC_KEPT, "filter": DOC_FILTERED}

_LIST_BY_LEVEL = {
    SOURCE_QUERY_CODE_PREFIX: source_document_crud.source_document_list_by_query,
    AREA_CODE_PREFIX: source_document_crud.source_document_list_by_area,
    RESEARCH_CODE_PREFIX: source_document_crud.source_document_list_by_research,
}


# Потолок кодов за вызов. Прогон блокирующий, и агент должен видеть, во что ввязывается:
# шесть кодов — это ещё обозримое ожидание, а не «а сколько это будет качаться».
SOURCES_REFETCH_MAX = 6

SKIP_NOT_FOUND = "not_found"
SKIP_NOT_A_SOURCE_CODE = "not_a_source_code"
SKIP_NOTHING_TO_FIX = "nothing_to_fix"


async def _sources_without_material(code: str) -> list[SourceDocumentWithPage] | str:
    """Источники в ``error`` под кодом — либо причина, по которой код ничего не дал.

    ``SOURCE@`` разбирается отдельно от уровней: у него единственного «нет такого» отличимо
    от «чинить нечего», у уровня пустой ответ значит и то, и другое.
    """
    prefix = code_prefix(code)
    bare = strip_prefix(code)
    if prefix == SOURCE_DOCUMENT_CODE_PREFIX:
        found = await source_document_crud.source_document_get(bare)
        if found is None:
            return SKIP_NOT_FOUND
        return [found] if found[0].status == DOC_ERROR else SKIP_NOTHING_TO_FIX
    level = _LIST_BY_LEVEL.get(prefix)
    if level is None:
        return SKIP_NOT_A_SOURCE_CODE
    return await level(bare, status=DOC_ERROR) or SKIP_NOTHING_TO_FIX


async def _collect_broken(
    codes: list[str],
) -> tuple[list[SourceDocumentWithPage], list[AgentSkippedCode]]:
    """Развернуть коды в источники без материала; каждый бесплодный код — строка отчёта.

    Источники складываются по своему коду: коды могут перекрываться (исследование и его же
    область), и без этого одну страницу качали бы дважды за вызов.
    """
    broken: dict[str, SourceDocumentWithPage] = {}
    skipped: list[AgentSkippedCode] = []
    for code in dict.fromkeys(codes):
        found = await _sources_without_material(code)
        if isinstance(found, str):
            skipped.append(AgentSkippedCode(code=code, reason=found))
            continue
        broken.update({doc.code: (doc, page) for doc, page in found})
    return list(broken.values()), skipped


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def sources_list(
        code: str, status: str | None = None
    ) -> list[ResearchSourceDocumentRow]:
        """List sources under a research / area / query, in search-launch order.

        The level is the kind of code you pass (RESEARCH@ / AREA@ / QUERY@); url/title come
        joined from the page. Sources are found by query_search_run — there is no manual create.

        Args:
            code: A RESEARCH@ / AREA@ / QUERY@ code — sources of that level.
            status: Optional filter — pending / kept / filtered / error.
        """
        level = _LIST_BY_LEVEL.get(code_prefix(code))
        if level is None:
            raise ValueError("code must be a RESEARCH@ / AREA@ / QUERY@ code.")
        rows = await level(strip_prefix(code), status=status)
        return [source_document_row(doc, page) for doc, page in rows]

    @mcp.tool()
    async def sources_refetch(codes: list[str]) -> AgentSourcesRefetched:
        """Download the material again for sources that have none. Takes up to 6 codes at once.

        Use it when sources came back `error`: fetching is terminal and never retries itself, so
        this is the only way to get their bodies. It re-downloads the pages, it does NOT search
        again — the found set does not change and no new sources appear. Blocking.

        `sources` lists what was actually re-downloaded, each with its new status: `pending`
        means the material arrived and the source is now yours to review, `error` means it failed
        again (typically the fetching service is down — tell the user rather than retrying in a
        loop). `skipped` lists the codes that produced nothing, with a reason: `nothing_to_fix`
        (no source without material there), `not_found` (no such source), `not_a_source_code`
        (not a SOURCE@ / QUERY@ / AREA@ / RESEARCH@ code). Codes may overlap — a research and its
        own area — without downloading anything twice.

        Args:
            codes: What to fix, 1..6 codes, levels may be mixed — SOURCE@ (one source), QUERY@
                (one search run), AREA@ or RESEARCH@ (everything under it).
        """
        if not codes:
            raise ValueError("Pass at least one code.")
        if len(codes) > SOURCES_REFETCH_MAX:
            raise ValueError(
                f"At most {SOURCES_REFETCH_MAX} codes per call, got {len(codes)}."
            )
        broken, skipped = await _collect_broken(codes)
        try:
            rows = await refetch_sources(broken)
        except RuntimeError as exc:
            raise ValueError(f"Cannot refetch: {exc}.") from exc
        return AgentSourcesRefetched(
            sources=[source_document_row(doc, page) for doc, page in rows],
            skipped=skipped,
        )

    @mcp.tool()
    async def source_get(source_code: str) -> AgentSourceDocumentDetail:
        """Return one source — assessment + url/title/body (joined from the page).

        A null `body` goes with status `error`: the page never downloaded. That state is
        terminal — the search run is over and nothing is fetching in the background, so
        re-reading the source will not produce a body. Do not fall back to `summary` (the search
        engine's snippet) as if it were the material.

        Args:
            source_code: The source code (from sources_list / query_search_run).
        """
        source_code = strip_prefix(source_code)
        result = await source_document_crud.source_document_get(source_code)
        if result is None:
            raise ValueError(f"Source {source_code} not found.")
        doc, page = result
        return agent_source_document_detail(doc, page)

    @mcp.tool()
    async def source_review(
        source_code: str, decision: str, relevance: int, note: str | None = None
    ) -> ResearchSourceDocumentRow:
        """Review a source in one call — decision + rating. Sets the source's status.

        Every source starts `pending` and must be reviewed; review them all before writing the
        area/research synthesis. A `keep` source is one you will cite in a body by its code.

        Args:
            source_code: The source to review.
            decision: `keep` (goes into the synthesis, cite it by its code) or `filter`
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
