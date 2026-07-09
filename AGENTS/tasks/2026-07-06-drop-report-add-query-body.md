# research: drop research_report, add research_query.body

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — per-query synthesis moves from a table into the query row

## Goal

research_report was an unplanned extra entity. Remove it; the per-query synthesis (its `content`)
moves into a new `body` column on research_query. research_query stops being a pure link table —
becomes "link + synthesis". Part of the wider prefix/restructure discussion (report gets no code).

## What was done

- **models/query.py**: + `body` (Text, nullable) after `query`; docstring — body = per-query
  synthesis, replaced research_report; row no longer fully immutable.
- **models/report.py**, **crud/report.py**, **mcp/report.py**: deleted.
- **models/__init__.py**: dropped ResearchReport export.
- **crud/query.py**: + `query_set_body(code, body)` (the body writer; body editor will reuse it);
  docstring updated.
- **crud/__init__.py**: entity list docstring (removed report).
- **dto.py**: removed ResearchReportRow / ResearchReportView; QueryDetail — `report` field →
  `body: str | None`.
- **api.py**: get_query returns `body=query_row.body`, no report fetch; dropped report_crud +
  ResearchReportRow imports.
- **mcp/__init__.py**: unregistered report surface; instructions — removed Report section, added a
  "per-query synthesis lives in the query body" note, fixed flow; header/mcp_server docstrings.
- **mcp/document.py**, **mcp/research.py**: "report" wording → "query synthesis" / "per-query and
  per-area syntheses".
- **module.py**: docstring + description (research/area/document/note; synthesis in query.body).
- **migrations**: rem_009_query_body (add column, down=drop), rem_010_report_drop (drop table;
  down recreates last shape — string query_code FK). Forward-only, applied on top.
- **bench**: dropped report_crud + research_report from reset list; report_create → query_set_body.

## Verification

- `migrate check` → pending rem_009/rem_010 only; `migrate upgrade` applied (now at head). PRAGMA:
  research_query has `body` (nullable, appended); research_report gone (0 rows).
- Smoke (temp sqlite): query.body None → set → read back; research.models/crud/mcp.report all
  ModuleNotFoundError (surface removed); mcp_server still imports/builds.
- `uv run pytest --core` — 266 passed; `vue-tsc --noEmit` — EXIT 0.

## Result

Per-query synthesis now lives in research_query.body (markdown, editable via the upcoming body
editor); research_report is gone. Body-bearing entities are now index/area/query/note — all will
take RSx codes + the common body editor. Deferred (next in the same wave): 3-letter prefixes
(incl. research_document → research_source / RSS_), body editor, canvas refresh (still shows the
dropped report + old 2-letter prefixes + "document"), web/dist, services/ orchestration.
