---
title: User-facing delete routes for research entities
date: 2026-08-27
status: in-work
description: "Added DELETE endpoints to /internal/research for research / area / source-query / note, mirroring the MCP delete tools and their manual cascades. Frontend UI wiring not done yet."
tags: [research, api]
---

## Task

«Нам нужны фронтовые (пользовательские) маршруты для удаления исследования, заметок и остального.
Проверь сущности, добавь маршруты».

## Entity audit (what can be deleted, and by whom)

| Entity | CRUD | MCP tool | HTTP route (before) | HTTP route (now) |
|---|---|---|---|---|
| `research_group` | `group_delete` (unshelves, keeps researches) | `group_delete` | `DELETE /groups/{code}` | unchanged |
| `research_index` | `research_delete` (cascade: sources → queries → notes → areas) | `research_delete` | — | `DELETE /researches/{code}` |
| `research_area` | `area_delete` (cascade: sources → queries) | `area_delete` | — | `DELETE /areas/{code}` |
| `research_source_query` | `source_query_delete` (cascade: sources) | `query_search_delete` | — | `DELETE /source-queries/{code}` |
| `research_note` | `note_delete` (no children) | `note_delete` | — | `DELETE /notes/{code}` |
| `research_source_document` | **none** | **none** | — | **deliberately none** |

- Cascades are **manual in CRUD** (sqlite FK-cascade is off), so the HTTP routes get them for free by
  calling the same CRUD the MCP tools call — no cascade logic duplicated in `api.py`.
- A single source has no delete anywhere: it is a row of a search run's output, disposed of by review
  (`kept` / `filtered`) or by deleting the whole run. Kept that way rather than inventing a
  `source_document_delete` that only the HTTP surface would have.
- `web_search` pages are **not** touched by any of these: a source references a page, it does not own
  it — the same page is shared across researches.

## What was done

- `src/modules/research/api.py` — four `DELETE` routes (204 on success, 404 via `ApiError.not_found`
  when the row is absent), each next to its entity's read routes; module docstring rewritten (it
  claimed the whole surface was read-only except groups).
- `tests/modules/research/test_api.py` — **15 tests** over a `_build_tree` helper (research → area →
  query → source on a real `web_search_page`, + note), exposed as two fixtures: `tree` and an
  independent `neighbour`.
  - Cascade shape: research takes everything under it; area takes its runs + sources but leaves the
    research and its notes; a run takes only its own sources; a note has no children.
  - Cascade scope (the manual `WHERE` of each step — sqlite has no FK cascade): the `neighbour` tree
    survives intact; sibling area / sibling run + its sources / sibling note survive.
  - Non-ownership: the `web_search_page` a deleted source pointed at is still there; a shelf survives
    its last research and its counter drops to 0.
  - Contract: 204 vs 404 for all four verbs, second delete of the same code is 404, a prefixed
    (`RESEARCH@…`) code is accepted, and the deleted children vanish from the research detail + the
    research from the list.
- `uv run pytest --module=research` — **173 passed**; full suite `uv run pytest -q` — **544 passed**.

## Left open

- Frontend is untouched: no `deleteResearch/Area/SourceQuery/Note` in
  `web/src/features/research/api.ts`, no buttons/confirm dialogs in the views, `web/dist` not rebuilt.
