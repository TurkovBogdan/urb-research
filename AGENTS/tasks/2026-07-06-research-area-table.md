# research: research_area table (RA_)

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — new level between research and query

## Goal

Add `research_area` (code `RA_<random_hash()>`) — a thematic section/direction inside a research
(research_index → research_area → research_query). Area = a knowledge sub-artifact with a two-layer
field set that doubles as an agent brief ("schema as prompt"):

- **scan layer** (for listing N areas): title (128), description (512) — "what this area is".
- **brief layer** (agent work): objective (1024), scope (1024, boundaries INCLUDE exclusions),
  expectations (1024, what the result looks like). Order: objective → scope → expectations.
- **result**: body (Text, unlimited, markdown synthesis of the section).
- **sort** (int, default 0) — sections are ordered.

Field sizes are enforced by **truncation in CRUD** (not validation errors), clipping by Unicode
**code points** (Cyrillic/multibyte safe — never cut mid-character), matching PG VARCHAR char
semantics; SQLite doesn't enforce VARCHAR length so the clip is the real bound.

New forward-only migration `rem_005_area` (no DB rebuild — the new policy's first application).

## Decisions

- `research_code` NOT NULL FK → research_index.code (CASCADE); area always belongs to a research.
- title NOT NULL; description/objective/scope/expectations/body nullable (incremental fill).
- No `constraints` field (folded into scope). No `enabled` (skip for now).
- `research_query` NOT repointed to area this iteration (still under research) — next decision.
- Frontend deferred — backend + MCP first.

## What was done

- **constants.py**: `AREA_TITLE_MAX=128`, `AREA_DESCRIPTION_MAX=512`, `AREA_BRIEF_MAX=1024`.
- **models/area.py** (new): `ResearchArea` — code(25) PK, research_code FK→research_index (CASCADE),
  title(128) NOT NULL, description(512), objective/scope/expectations(1024), body(Text), sort(int,0),
  timestamps. Index on research_code. Field order: objective → scope → expectations (no constraints —
  folded into scope's boundaries).
- **models/__init__.py**: register `ResearchArea`.
- **migrations/rem_005_area.py** (new, forward-only, down=rem_004): creates research_area. Applied via
  `migrate upgrade` on top of existing schema — **no DB rebuild, existing data intact** (first use of the
  new policy). Dev backend's lifespan had already applied it on hot-reload → `migrate upgrade` = nothing to apply.
- **crud/area.py** (new): `area_code()`=`RA_<random_hash()>`; `_clip(value, limit)` truncates by Unicode
  code points (Cyrillic/multibyte safe, matches PG VARCHAR char semantics, real bound on SQLite);
  `area_create` (clips capped fields), `area_get`, `area_list_by_research` (order sort→created_at→code),
  `area_update` (clip on provided; body unlimited), `area_count_by_research_codes`.
- **dto.py**: `AreaRow` (scan: code/research_code/title/description/sort) + `AreaDetail`
  (+objective/scope/expectations/body); `ResearchDetail` gains `areas: list[AreaRow]`.
- **api.py**: `get_research` returns `areas`; new `GET /areas/{area_code}` → AreaDetail.
- **mcp/area.py** (new) + registered in mcp server: `area_add`, `research_areas`, `area_get`, `area_update`;
  instructions rewritten (research → area → query; scan layer vs brief). 20 tools total.

## Verification

- `migrate check` up to date; research_area present, other research tables + data untouched (no rebuild).
- In-memory smoke: RA_ code (len 25); Cyrillic truncation title→128 / description→512 / brief→1024 with no
  mid-character break (all chars intact); body unlimited (5000 kept); re-clip on update; list/count/get-missing.
- `uv run pytest --core` — 266 passed; `vue-tsc --noEmit` — EXIT 0; MCP build registers the 4 area tools.

## Problems

None.

## Result

`research_area` (RA_) is the mid level research_index → research_area → research_query, a two-layer
knowledge sub-artifact: scan (title/description) + brief (objective/scope/expectations) + body + sort.
Sizes enforced by Cyrillic-safe truncation in CRUD. Not yet done (next decisions): repoint research_query
to areas (direction_code), frontend area views, `web/dist` rebuild.
