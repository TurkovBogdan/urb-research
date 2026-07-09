# research: add note kind `clarification`

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — research_note kinds

## Goal

Add a sixth `research_note` kind — `clarification` (a clarification / constraint the user gives
that steers or narrows the research: scope, priorities, definitions). Distinct from `decision`
(the agent's own methodological choice) — clarification = what the user told you.

## What was done

- **constants.py**: added `NOTE_CLARIFICATION = "clarification"`; extended `NOTE_KINDS` + `__all__`.
- **migration rem_014_note_kind_clarification** (forward-only): widens the `ck_research_note_kind`
  CHECK from five to six kinds via `batch_alter_table` (SQLite can't ALTER a CHECK in place; same
  op runs on Postgres). Downgrade narrows back to the original five.
- **mcp/note.py**: `note_add` / `note_update` docstrings list `clarification` and describe it
  vs `decision`. (`_require_kind` + model CHECK read `NOTE_KINDS` — no code branch to touch.)
- **mcp/__init__.py**: server Notes instruction mentions the sixth kind.
- **canvas** research-tables.canvas: research_note node kind line updated.

## Verification

- `migrate upgrade` applied rem_014; `migrate check` up to date.
- dev sqlite (read-only) DDL: `ck_research_note_kind CHECK (kind IN ('result','idea','question',
  'memory','decision','clarification'))` — name preserved, sixth value present.
- Import smoke: `NOTE_KINDS` contains `clarification`; note tool module compiles.
- `--core` 266 passed.

## Result

research_note accepts six kinds. Deferred (unchanged): 3-letter prefixes, body editor,
web/dist, services/.
