# research: rename query/document → source_query/source_document

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — the external-material tables become "sources"

## Goal

Make the research module speak *sources*, not "documents" (a document is a source; "source
document" clunk = the redundancy the user flagged). Group the two external-material tables under a
`source` sub-domain:

- research_query → **research_source_query** (источниковый запрос — the search that gathers sources;
  also disambiguates from web_search_query)
- research_document → **research_source_document** (источник — a found+assessed source)

Code prefixes (RQ_/RD_) unchanged — the 3-letter prefix change is a separate later step.

## Naming split (agent vs developer)

- **DB / models / crud / dto** use the full leaf: `source_query_*` / `source_document_*`,
  `ResearchSourceQuery` / `ResearchSourceDocument`, `ResearchSourceQueryRow` /
  `ResearchSourceDocumentRow` / `SourceQueryDetail`.
- **Agent-facing MCP tools** use short terms: **source** (the found item) and **query** (the
  search). So document_* tools → `source_*` (source_add/get/keep/filter/set_relevance/set_summary/
  mark_fetch_error, param `source_code`), `query_documents` → `query_sources`; the query link stays
  `query_link` / `research_queries`. Agent never sees table names.

## What was done

- **Files (mv):** models/{query,document}.py → models/{source_query,source_document}.py;
  crud/{query,document}.py → crud/{source_query,source_document}.py; mcp/document.py →
  mcp/source_document.py.
- **models:** ResearchQuery→ResearchSourceQuery, ResearchDocument→ResearchSourceDocument;
  __tablename__ research_source_query / research_source_document; constraint/index names
  (uq_/ix_/ck_research_source_*); document FK query_code → research_source_query.code. __init__ +
  research.py/constants.py docstrings updated.
- **crud:** functions query_*→source_query_* (create/get/list_by_research/list_by_area/set_body/
  count_by_research_codes), document_*→source_document_*; prefix consts SOURCE_QUERY_CODE_PREFIX /
  SOURCE_DOCUMENT_CODE_PREFIX (values still RQ_/RD_); DocumentWithPage→SourceDocumentWithPage.
- **dto:** class + builder renames (source_document_row/detail, _source_document_fields);
  ResearchDetail.queries + SourceQueryDetail.documents retyped.
- **api:** endpoints /queries → /source-queries, /documents → /source-documents; crud/dto renames.
- **mcp:** source_document surface (source_* tools); research.py (query_link/research_queries →
  ResearchSourceQueryRow + source_query crud); __init__ instructions rewritten (Sources section,
  flow); module.py docstring.
- **bench:** source_query_* / source_document_* crud; _RESET_TABLES new names.
- **migration rem_011_source_tables** (forward-only): dev empty → drop research_document +
  research_query, create research_source_query (with body) + research_source_document (new
  constraint/index names). Downgrade recreates the old pair.

## Verification

- `migrate check`→pending rem_011 only; `migrate upgrade` applied. Tables now: research_area,
  research_index, research_note, research_source_document, research_source_query (no query/document/
  report).
- Smoke (temp sqlite): source_query_create RQ_, source_document_create RD_ (status pending), JOIN
  pulls url/title from web_search_page, source_query_set_body writes/reads, mcp_server imports.
- MCP surface built via fake registry: 23 tools, no duplicates (source_add/get/keep/filter/
  set_relevance/set_summary/mark_fetch_error, query_sources, query_link, …).
- `uv run pytest --core` — 266 passed; `vue-tsc --noEmit` — EXIT 0.

## Result

The research module now speaks sources: research_source_query (the sourcing search, +body synthesis)
and research_source_document (a found+assessed source), with agent tools named source_*/query_*.
Deferred (next in the wave): 3-letter code prefixes (RQ_→RSQ_, RD_→RSS_?, etc.), the common body
editor (index/area/source_query/note), canvas refresh, web/dist, services/ orchestration.
