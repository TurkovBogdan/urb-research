# research: drop research_area.sort

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — remove the unused area ordering hint

## Goal

`research_area.sort` is not needed — areas are ordered by `created_at` (creation order).

## What was done

- **models/area.py**: dropped `sort` column (+ unused Integer import); docstring — areas ordered
  by created_at.
- **crud/area.py**: removed `sort` from area_create / area_update; area_list_by_research orders by
  created_at, code.
- **dto.py**: AreaRow lost `sort`.
- **mcp/area.py**: area_add / area_update lost the `sort` param + docstrings; research_areas doc
  "oldest first". mcp/__init__ instructions: area_add signature.
- **migration rem_012_area_drop_sort** (forward-only): drop column; downgrade re-adds (int, def 0).
- **canvas** research-tables.canvas: removed the `sort (int, def 0)` line from research_area.

## Verification

- `migrate upgrade` applied; PRAGMA research_area has no `sort` (body → created_at → updated_at).
- Smoke: area_create (no sort) / area_list ordered by creation (A1, A2) / area_update(body) — ok;
  no `sort` attr on the model.
- No leftover `sort` refs in live code; `--core` 266 passed; `vue-tsc` EXIT 0; canvas JSON valid.

## Result

research_area has no ordering column; areas list in creation order. Deferred (unchanged): 3-letter
prefixes, body editor, web/dist, services/.
