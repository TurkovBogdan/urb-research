# research: research_note — typed working-memory note (RN_)

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — free note entity attached to a research

## Goal

Add a note entity: a research's free working memory — what the agent records along the way that
does NOT belong to a single document or area (a finding, hypothesis, open question, raw
observation, methodological decision). Not the output structure (that's the area) — a
self-contained typed mini-artifact.

## Design (discussed field-by-field)

Fields (mirrors research_index's description fields + a required type):
- code (RN_ PK, random_hash)
- research_code (FK research_index CASCADE) — attached to the research only (no area link; dropped)
- **kind** (required, no default — forces the agent to classify: "schema as prompt")
- title (≤128) / description (≤512, nullable) / body (Text, unlimited, nullable)
- created_at / updated_at

Kinds (`NOTE_KINDS`): `result` (established finding) · `idea` (hypothesis / direction) ·
`question` (open gap) · `memory` (raw observation / context) · `decision` (methodological
choice — what was included/excluded). CHECK constraint. No `reference`/`summary` (subsumed by
result/memory or belong to area/report).

Rejected: area_code link (user: not needed); a title-less one-liner (user: use the typical
title/description/body description fields); a default kind (kept required — classification is
the point).

## What was done

- **constants.py**: NOTE_TITLE_MAX(128)/NOTE_DESCRIPTION_MAX(512) + NOTE_RESULT/IDEA/QUESTION/
  MEMORY/DECISION + NOTE_KINDS (reuses sql_in for the CHECK).
- **models/note.py**: `ResearchNote` — code(RN_ PK), research_code(FK CASCADE), kind, title/
  description/body, timestamps. CHECK kind IN NOTE_KINDS; index on research_code.
- **models/__init__.py**: register ResearchNote.
- **migrations/rem_008_note.py** (forward-only, down=rem_007): create research_note (new table,
  applied on top — nothing to rebuild).
- **crud/note.py**: NOTE_CODE_PREFIX=RN_; note_create (clips title/description by code points,
  Cyrillic-safe; body unlimited), note_get, note_list_by_research (created_at asc, code asc),
  note_update (None=keep), note_delete.
- **dto.py**: NoteRow (scan layer: code/research_code/kind/title/description/dates) + NoteDetail
  (+body); ResearchDetail gained `notes: list[NoteRow]`.
- **api.py**: notes in get_research detail; GET /notes/{note_code} → NoteDetail.
- **mcp/note.py**: note_add(research_code, kind, title, description?, body?), research_notes,
  note_get, note_update, note_delete. `_require_kind` rejects unknown kind before insert.
- **mcp/__init__.py**: register note surface + instructions (Notes section, flow note).

## Verification

- `migrate check` → pending rem_008 only; `migrate upgrade` applied (now at head). PRAGMA: 8-col
  research_note (code/research_code/kind/title NOT NULL, description/body nullable).
- Smoke (temp sqlite): RN_ code; Cyrillic title intact; get/list/update/delete; title 200→128
  clip by code points; CHECK kind → IntegrityError on bogus; NOTE_KINDS = 5.
- `uv run pytest --core` — 266 passed; `vue-tsc --noEmit` — EXIT 0.

## Result

research_note is the research's typed working memory — result/idea/question/memory/decision,
title/description/body, attached to the research. Complements areas (output structure), not a
replacement. Note: research module still has no test suite and is not in build_modules/test
registry (pre-existing); no docs/research/INDEX.md hub yet (module-wide gap). Deferred (unchanged):
frontend note/area views, 3-letter prefixes, web/dist rebuild, services/ orchestration.
