"""MCP-сервер ``research`` — реестр исследований + областей + источников + заметок.

``mcp_server(ctx)`` — конструктор (``McpServerBuilder``), кладётся в
``ResearchModule.mcp_servers["research"]``. Импорт ``make_mcp_server``
(→ ``fastmcp``) ОТЛОЖЕН в тело функции: объявление словаря в ``module.py`` ссылается
на функцию, не вызывая её, → ``build_modules()`` не тянет форк. Регистрирующие
модули (research/area/source_document/note) держат ``FastMCP`` только под TYPE_CHECKING.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.mcp.area import register as _register_area
from src.modules.research.mcp.body import register as _register_body
from src.modules.research.mcp.note import register as _register_note
from src.modules.research.mcp.research import register as _register_research
from src.modules.research.mcp.source_document import register as _register_source_document

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from src.core.mcp import McpServerContext

_INSTRUCTIONS = (
    "Research registry MCP server — turns a topic into a cited, structured write-up backed by "
    "reviewed web sources. It is your durable memory for a research: everything you create here "
    "is shown to the user in the app, so treat it as the deliverable, not a scratchpad.\n\n"
    "CODES. Every entity has a code tagged type@hash — RESEARCH@ (a research), AREA@ (a section), "
    "NOTE@ (a note), QUERY@ (a search run), SOURCE@ (a found source). Always pass a code back exactly "
    "as you received it, with its tag. The hierarchy is research → area → search (query) → source; "
    "notes hang off the research.\n\n"
    "─── THE PIPELINE (follow it in order) ───\n"
    "1. research_create(title, description?) — open the research. Keep the body for the final synthesis.\n"
    "2. area_create(research_code, title, description?, objective?, scope?, expectations?) — break the "
    "topic into a few focused areas (thematic directions / report sections). Fill the brief "
    "(objective / scope / expectations) up front: it is the plan for that area.\n"
    "3. For EACH area, do a search-and-review cycle (see below). Areas are independent.\n"
    "4. Write each area's synthesis into its body, citing the sources you kept (see CITATIONS).\n"
    "5. Assemble the research body from the area findings; drop notes for anything cross-cutting.\n\n"
    "─── SEARCH & REVIEW ONE AREA (delegate to a sub-agent) ───\n"
    "RECOMMENDED: research one area per sub-agent. Hand the sub-agent the area code and let it own that "
    "area end to end — run the searches, review every source, write the area body. query_search_run is "
    "blocking and each run returns many sources that each need reading and judging, so one area is a "
    "full unit of work; areas are independent, so sub-agents parallelize cleanly and keep each context "
    "focused on one section.\n"
    "Within an area the cycle is:\n"
    "  a. query_search_run(area_code, query) — run a web search for the area (blocking). It records the "
    "run and returns the sources it found, each with status `pending`. Run it several times with "
    "different queries to cover the area's scope.\n"
    "  b. REVIEW EVERY SOURCE — this is mandatory, not optional. Each source starts `pending`; a source "
    "left `pending` is unfinished work. For each: source_get(source_code) to read the page body, then "
    "source_review(source_code, decision, relevance, note?) — decision `keep` (you will cite it) or "
    "`filter` (irrelevant / low quality / duplicate — say why in note), relevance 1..10 (1 = junk, "
    "5 = medium or duplicate, 10 = key). Filter hard: keep only sources you will actually use. "
    "sources_list(code, status?) tracks progress — sources_list(area_code, status='pending') must end "
    "empty before you write the synthesis.\n"
    "  c. Write the area body from the KEPT sources, citing each one.\n\n"
    "─── CITATIONS (how sources reach the user) ───\n"
    "When you write a body (research / area / note), cite the sources you used inline by their code, "
    "as SOURCE@<code>. These render in the user's interface as a link to the source — it is how the "
    "reader gets from a claim to its evidence, so every non-trivial claim should carry the SOURCE@ code "
    "of a source you reviewed and KEPT. Do not cite a source you filtered or never reviewed, and do not "
    "invent codes — only use codes returned by query_search_run / sources_list.\n\n"
    "─── TOOLS BY GROUP ───\n"
    "Research: research_create(title, description?, body?) → its code; research_get(research_code) — the "
    "research with its body, areas and notes; research_list() — all researches, recently updated first; "
    "research_update(research_code, title?, description?, body?) — edit fields (omit to keep); "
    "research_delete(research_code) — remove it and everything under it (cascade).\n"
    "Areas: area_create(...) (above) → its code; areas_list(research_code) — the scan list; "
    "area_get(area_code) — the area with its brief and body; area_update(area_code, title?, description?, "
    "objective?, scope?, expectations?, body?) — edit; area_delete(area_code) — remove the area with its "
    "searches and sources (cascade).\n"
    "Searches & sources: query_search_run(area_code, query) (above); query_search_list(code) — the "
    "searches of an AREA@ or RESEARCH@; query_search_delete(query_code) — remove a run and its sources; "
    "sources_list(code, status?) — sources of a RESEARCH@ / AREA@ / QUERY@ (optional status filter: "
    "pending / kept / filtered / fetch_error); source_get(source_code) — one source with the page body; "
    "source_review(source_code, decision, relevance, note?) (above). Sources are found by search only — "
    "there is no manual source-create.\n"
    "Notes: the research's working memory — a self-contained mini-artifact (title, description?, body?) "
    "not tied to one source or area. note_create(research_code, kind, title, description?, body?) → its "
    "code; kind is required — `result` (an established finding), `idea` (a hypothesis), `question` (an "
    "open gap), `memory` (a raw observation to keep), `decision` (your methodological choice), "
    "`clarification` (a constraint the user gave). notes_list(research_code, kind?); "
    "note_get / note_update / note_delete.\n"
    "Body editor (RESEARCH@ / AREA@ / NOTE@ — searches and sources have no editable body): "
    "body_edit(code, action, text, find?, heading?) with action set / replace (unique find) / "
    "replace_block (a `#`/`##` heading block); body_add(code, text, position, anchor?) with position "
    "start / end / before / after (relative to anchor). Both return the updated body. Use these for "
    "incremental edits instead of rewriting the whole body with *_update."
)


def mcp_server(ctx: "McpServerContext") -> "FastMCP":
    """Собрать MCP-сервер ``research`` с поверхностями research/area/source_document/note."""
    from src.core.mcp import make_mcp_server

    mcp = make_mcp_server("research", _INSTRUCTIONS, ctx)
    _register_research(mcp)
    _register_area(mcp)
    _register_source_document(mcp)
    _register_note(mcp)
    _register_body(mcp)
    return mcp


__all__ = ["mcp_server"]
