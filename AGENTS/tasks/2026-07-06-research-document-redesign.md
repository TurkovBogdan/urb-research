# research: research_document redesign (RD_, ref web_search, statuses)

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — research_document as a reference + assessment record

## Goal

Redesign research_document: no copies of page data — reference web_search_page and JOIN. Store only
links + research assessment. Code PK RD_.

Fields: code(RD_ PK) · research_code · area_code · query_code (all FK CASCADE) · page_code (soft-ref →
web_search_page WD_, no FK) · status · relevance(int 1-10) · summary(local snapshot) · note · created_at ·
updated_at. `unique(query_code, page_code)`. CHECK status IN(fetch_error,pending,kept,filtered) + CHECK
relevance BETWEEN 1 AND 10.

Dropped columns url/title/content — joined from web_search_page (url/domain/title/body). filtered(bool)+
filter_reason → status(enum)+note. relevance float→int.

Statuses: **fetch_error** (page load failed, kept for integrity) / **pending** (fetched, unreviewed,
default) / **kept** (reviewed, relevant) / **filtered** (explicitly rejected, reason in note). Machine
pending → kept|filtered; fetch_error terminal at entry. kept/filtered = explicit agent decision;
relevance is a separate 1-10 score.

Same doc in two researches: shared page (deterministic page_code, one web_search_page row), isolated
assessment (research_document per query_code+page_code). No schema change needed for that.

## Integration (join по умолчанию)

Read joins research_document → web_search_page (page_code = code) for url/domain/title/body. summary is
LOCAL (snapshot from web_search_query_result at add time). Cross-module: research crud imports WebSearchPage
for the read join (research is the consumer of the raw-data module).

## What was done

- **constants.py**: DOC_FETCH_ERROR/PENDING/KEPT/FILTERED + DOC_STATUSES; re-added sql_in (for the CHECK).
- **models/document.py**: rewritten — code(RD_ PK), research_code/area_code/query_code (FK CASCADE),
  page_code (soft-ref, NOT NULL), status (default pending), relevance(int), summary, note, timestamps.
  unique(query_code, page_code); CHECK status; CHECK relevance BETWEEN 1 AND 10. Dropped url/title/content/
  filtered/filter_reason.
- **migrations/rem_007_document.py** (forward-only, down=rem_006): drop+recreate research_document (empty).
- **crud/document.py**: rewritten — document_code()=RD_; document_create(research/area/query/page_code,
  summary, status); reads **join web_search_page** (`document_get`/`document_list_by_query` → (doc, page)
  tuples, outerjoin on page_code); setters document_set_relevance/summary/status.
- **dto.py**: ResearchDocumentRow (own fields + url/domain/title from join) + ResearchDocumentDetail (+body);
  builders `document_row(doc,page)` / `document_detail(doc,page)`.
- **api.py**: get_document(document_code) → join detail; get_query documents via document_row.
- **mcp/document.py**: rewritten — document_add(query_code, page_code, summary?) (research/area from query),
  document_get (joined body), query_documents (joined url/title), document_set_relevance(1..10),
  document_set_summary, document_keep, document_filter(note), document_mark_fetch_error; removed
  document_set_content. mcp/report.py sources via document_row. Instructions rewritten. 20 tools.
- **bench**: documents now seed a web_search_page (page_upsert + page_set_body) and reference it by
  page_code; relevance float→int(1..10); filtered→document_set_status(FILTERED)/else KEPT.

## Verification

- `migrate check` up to date; PRAGMA confirms 11-col research_document (page_code NOT NULL, relevance nullable).
- Smoke: RD_ code, status pending; JOIN pulls url/domain/title/body from web_search_page; summary local;
  set_relevance(9)/status filtered+note; CHECK relevance 1–10 → IntegrityError on 99; unique(query,page) → IntegrityError.
- `uv run pytest --core` — 266 passed; `vue-tsc --noEmit` — EXIT 0; MCP 20 tools (document surface reworked,
  document_set_content gone).

## Problems

None. Cross-module coupling introduced deliberately: research crud/dto import WebSearchPage for the read
join (research = consumer of the web_search raw-data module), per the "join по умолчанию" decision.

## Result

research_document is now a reference + assessment: no page-data copies, url/domain/title/body joined from
web_search_page by page_code; summary is a local snapshot. Four statuses (fetch_error/pending/kept/filtered),
relevance 1–10 (int, separate from keep/filter). Same doc in two researches → shared page, isolated rows.
Deferred: frontend document/query views, 3-letter prefixes, `web/dist` rebuild, full pipeline orchestration
(services/).
