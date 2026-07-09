# research: research_area → title/description/body pattern

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — area conforms to the artifact pattern

## Goal

research_area broke the title/description/body pattern shared by research_index / research_note —
it wedged a brief (objective / scope / expectations) between description and body. Chosen option A:
drop the three brief columns so area = title/description/body; the brief becomes guidance in the
area_add tool description that the agent folds into body.

## What was done

- **constants.py**: dropped AREA_BRIEF_MAX (kept AREA_TITLE_MAX / AREA_DESCRIPTION_MAX).
- **models/area.py**: removed objective/scope/expectations columns; docstring — area is a
  title/description/body artifact, brief lives in the area_add prompt.
- **crud/area.py**: area_create / area_update lost the three params (+ AREA_BRIEF_MAX import).
- **dto.py**: AreaDetail = AreaRow + body only.
- **mcp/area.py**: area_add(research_code, title, description?) / area_update(title?, description?,
  body?); the brief (objective / scope+boundaries / expected result) is now written into the
  docstring as guidance to fold into body/description. area_get returns title/description/body.
- **mcp/__init__.py**: Areas instructions rewritten (title/description/body + brief guidance).
- **migration rem_013_area_drop_brief** (forward-only): drop objective/scope/expectations;
  downgrade re-adds (String(1024) nullable).
- **canvas** research-tables.canvas: research_area node trimmed to title/description/body + a note
  that the brief lives in the area_add prompt.

## Verification

- `migrate upgrade` applied; PRAGMA research_area = code/research_code/title/description/body/
  created_at/updated_at (brief gone).
- Smoke: area_create(title, description) / area_update(body); no objective/scope/expectations attrs;
  mcp_server builds.
- No leftover brief column/param refs (only session_scope / auth scope false positives + the
  intentional brief prose in the area_add prompt); `--core` 266; `vue-tsc` EXIT 0; canvas valid.

## Result

All knowledge artifacts (research_index, research_area, research_note) now share title/description/
body; the area brief is a forcing instruction in area_add, not columns. Deferred (unchanged):
3-letter prefixes, body editor (index/area/source_query/note), web/dist, services/.
