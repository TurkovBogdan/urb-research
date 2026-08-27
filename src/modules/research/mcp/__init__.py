"""MCP-сервер ``research`` — реестр исследований + областей + источников + заметок.

``mcp_server(ctx)`` — конструктор (``McpServerBuilder``), кладётся в
``ResearchModule.mcp_servers["research"]``. Импорт ``make_mcp_server``
(→ ``fastmcp``) ОТЛОЖЕН в тело функции: объявление словаря в ``module.py`` ссылается
на функцию, не вызывая её, → ``build_modules()`` не тянет форк. Регистрирующие
модули (group/research/area/source_document/note/body/interface) держат ``FastMCP`` только под
TYPE_CHECKING.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.mcp.area import register as _register_area
from src.modules.research.mcp.body import register as _register_body
from src.modules.research.mcp.group import register as _register_group
from src.modules.research.mcp.interface import register as _register_interface
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
    "CODES. Every entity has a code, and the code says what it is — RESEARCH@… (a research), "
    "AREA@… (a section), NOTE@… (a note), QUERY@… (a search run), SOURCE@… (a found source), "
    "GROUP@… (a group researches are filed under). Always pass a code back whole, exactly as you "
    "received it. The "
    "hierarchy is research → area → search (query) → source; notes hang off the research, and "
    "groups sit above researches as pure filing.\n\n"
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
    "     A source whose page failed to download comes back `error`, not `pending`, and has no "
    "body. Nothing loads later on its own — never wait or re-poll for a body, and never judge such "
    "a source from its `summary`, which is the search engine's snippet rather than the material. "
    "Call sources_refetch(codes) to download the material again (it does not search again) — pass "
    "up to 6 codes at once, so one call fixes a whole area; what comes back `pending` is yours to "
    "review, what stays `error` is a service that is down — say so to the user instead of "
    "looping.\n"
    "  b. REVIEW EVERY SOURCE — this is mandatory, not optional. Each source starts `pending`; a source "
    "left `pending` is unfinished work. For each: source_get(source_code) to read the page body, then "
    "source_review(source_code, decision, relevance, note?) — decision `keep` (you will cite it) or "
    "`filter` (irrelevant / low quality / duplicate — say why in note), relevance 1..10 (1 = junk, "
    "5 = medium or duplicate, 10 = key). Filter hard: keep only sources you will actually use. "
    "sources_list(code, status?) tracks progress — sources_list(area_code, status='pending') must end "
    "empty before you write the synthesis.\n"
    "  c. Write the area body from the KEPT sources, citing each one.\n\n"
    "─── CITATIONS & CROSS-LINKS (how a body reaches the user) ───\n"
    "Any code you write into a body becomes a link to that entity's page in the user's interface — "
    "a source, an area, a note, a search, a research alike. Write the code as it is, in the running "
    "text: it needs no escaping and no wrapping in backticks, quotes, brackets or parentheses. The "
    "link is labelled with the entity's own title, so the code itself is never shown to the reader "
    "— write around it as if the title stood there.\n"
    "Cite with it: every non-trivial claim should carry the code of a source you reviewed and KEPT — "
    "that is how the reader gets from a claim to its evidence. Do not cite a source you filtered or "
    "never reviewed, and do not invent codes — only use codes returned by query_search_run / "
    "sources_list.\n"
    "Cross-link with it too: point at a sibling area, a note or a search by its code rather than by "
    "name, so the reader can jump there and the reference survives a rename.\n\n"
    "─── TOOL REFERENCE ───\n"
    "Research: research_create(title, description?, body?, group_code?) → its code; "
    "research_get(research_code) — the research with its body, areas and notes; "
    "research_list(group_code?) — researches, recently updated first, optionally only those in one "
    "group (empty string = only the ungrouped ones); "
    "research_update(research_code, title?, description?, body?, group_code?) — edit fields (omit to keep); "
    "research_delete(research_code) — remove it and everything under it (cascade).\n"
    "Areas: area_create(...) (above) → its code; areas_list(research_code) — the scan list; "
    "area_get(area_code) — the area with its brief and body; area_update(area_code, title?, description?, "
    "objective?, scope?, expectations?, body?) — edit; area_delete(area_code) — remove the area with its "
    "searches and sources (cascade).\n"
    "Searches & sources: query_search_run(area_code, query) (above); query_search_list(code) — the "
    "searches of an AREA@ or RESEARCH@; query_search_delete(query_code) — remove a run and its sources; "
    "sources_list(code, status?) — sources of a RESEARCH@ / AREA@ / QUERY@ (optional status filter: "
    "pending / kept / filtered / error); source_get(source_code) — one source with the page body; "
    "sources_refetch(codes) — re-download the material for the `error` sources under up to 6 "
    "SOURCE@ / QUERY@ / AREA@ / RESEARCH@ codes, returning the sources it touched plus the codes "
    "it skipped and why; "
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
    "incremental edits instead of rewriting the whole body with *_update.\n"
    "Showing the user: interface_open(code) — opens that entity's page in the user's browser and "
    "returns the address. Takes any code (RESEARCH@ / AREA@ / NOTE@ / QUERY@ / SOURCE@ / GROUP@, "
    "and SEARCH@ / PAGE@ for the underlying web search). Use it when the user asks to see "
    "something or when you have finished work worth looking at — it puts the artifact on screen "
    "instead of describing it. It acts on the user's machine, so do not fire it after every call.\n"
    "Groups (optional, low priority): folders for the research list. A research MAY be filed in "
    "one — pass group_code to research_create / research_update (empty string takes it out of the "
    "group) — and research_get / research_list report group_code + group_name, where group_name is "
    "derived from the group and is not editable on the research. Grouping is cosmetic filing, not "
    "part of the research pipeline: leave a research ungrouped unless the user asked for groups. "
    "group_create(title, description?) → its code; group_list(); group_get; group_update; "
    "group_delete — deleting a group KEEPS its researches, they just become ungrouped. How a "
    "group looks and where it sits in the list is the user's to set in the interface — you only "
    "name it and file researches into it."
)


def mcp_server(ctx: "McpServerContext") -> "FastMCP":
    """Собрать MCP-сервер ``research`` с поверхностями research/area/source_document/note."""
    from src.core.mcp import make_mcp_server

    mcp = make_mcp_server("research", _INSTRUCTIONS, ctx)
    _register_group(mcp)
    _register_research(mcp)
    _register_area(mcp)
    _register_source_document(mcp)
    _register_note(mcp)
    _register_body(mcp)
    _register_interface(mcp)
    return mcp


__all__ = ["mcp_server"]
