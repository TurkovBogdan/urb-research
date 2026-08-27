---
title: Project onboarding study
date: 2026-08-26
status: completed
description: "User asked to study the project. Read the records (memory router, tasks/docs/tools indexes), walked the source tree (app entry, module composition, research + web_search modules), and verified the suite is green."
tags: [onboarding, research, web_search]
---

## Task

«Изучай проект» — get up to speed on the codebase before further work.

## Context

New session; no prior context in this conversation. `MEMORY.md` is over its size limit
(30.1 KB vs 24.4 KB) and only partially loaded, so parts of the routing table were
missing from context and had to be recovered from the code.

## What was done

- Read `AGENTS/tasks/INDEX.md` (page 1), `AGENTS/docs/INDEX.md`, `AGENTS/tools/INDEX.md`.
- Walked `src/`: `app.py` roles (`--backend` / `--worker` / `--mcp-stdio` / `migrate`),
  `apps/app/modules.py` (6 modules), `core/` layout.
- Read the `research` module in depth: `module.py`, `mcp/__init__.py` (agent instructions +
  23-tool surface), `constants.py`, `codes.py` (bare-hash storage + `TYPE@hash` presentation),
  all five ORM models; skimmed `web_search` layout (engines/providers/searcher).
- Ran `uv run pytest -q` — **446 passed** (default markers `pure` + `db`).

## Result

No code changed — read-only onboarding. Observations worth carrying forward:

- `AGENTS/memory/MEMORY.md` exceeds its size budget; the `core_connectors` and `web_search`
  router entries are multi-hundred-word paragraphs that belong in their doc hubs
  (`agent-docs-maintenance.md` playbook applies).
- `docs/research/INDEX.md` does not exist — `research` is the only module with an MCP surface
  and has no doc hub (already noted as a loose end in task 2026-07-06-research-mcp-returns).
- The tasks index "In work" table holds several rows marked **Completed** in their own text
  (e.g. 07-09 secret audit, 07-08 stdio config) that were never moved to "Completed".
