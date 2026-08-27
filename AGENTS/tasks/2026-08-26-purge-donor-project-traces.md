---
title: Purge donor-project traces
date: 2026-08-26
status: completed
description: "Remove every trace of the donor project this repo's core was forked from — name, brand strings, paths, DB names, IDE identifiers — across instructions, docs, memory, tasks/plans, code and config. Done via a four-way subagent fan-out over disjoint zones."
tags: [records, config, branding]
---

## Task

«Я использовал ядро другого своего проекта из экосистемы семафора, но тут информации о нём
не должно остаться. Вычищай через саб агентов.»

## Context

The repository was forked from a donor platform core. `AGENTS/agent-primary.md` (symlinked as
`CLAUDE.md` / `AGENTS.md`, loaded into every session) still opened with the donor's «About the
project» block, and the donor name leaked into 45 files — records, config, the FastAPI app title,
test fixtures, frontend demo strings and the committed SPA bundle.

Purged: the donor's project/package name in all its spellings, its product brand and the legacy
brand it replaced, its binary names, its private-store symlink paths, its DB names and its
fixture credentials. The concrete strings are deliberately **not** listed here — writing them
down would defeat the purge.

Project identity going forward: repo/package **urb-research**, UI brand **Uroboros.Research**
(`web/index.html` `<title>`).

## What was done

Inventory first (`grep` over the tree, excluding `.git` / `.venv` / `runtime` / `node_modules`),
then a four-subagent fan-out over disjoint zones:

- **A** — `AGENTS/agent-primary.md` + `AGENTS/docs/**` + `AGENTS/research/openrouter`.
  Also the donor's stale factual claims: module list, «PostgreSQL DB», «SPA served by nginx,
  never by the backend» (contradicts `core/router/spa.py`), dead `dev/docs/*` links, `core_users`.
- **B** — `AGENTS/memory/**`.
- **C** — `AGENTS/tasks/**` + `AGENTS/plans/**` (historical records: meaning kept, name dropped).
- **D** — code/config: `pyproject.toml` (+ `uv lock`), `web/package.json`, `.env` / `.env.example.*`,
  `.gitignore`, `dev/.run/*.xml`, `dev/bench`, `src/core/app_factory.py` (`title=`),
  `tests/core/{_support,test_guards}.py`, design-system demo strings + the matching `web/dist`
  chunks (pnpm absent → no rebuild possible).

Removed by hand: the `AGENTS/` symlink pointing into the donor repo (gitignored, local-only;
its target on disk untouched).

Hard constraint given to every subagent: `asyncio.Semaphore` and `semaphore`/`_semaphore`
identifiers are a concurrency primitive, not the donor's name — untouched.

## Result

**50 files cleaned across the four zones; a repo-wide control grep for every purged spelling now
returns zero hits** (excluding `.git` / `.venv` / `runtime` / `node_modules`).

- **Docs/instructions (6)** — `agent-primary.md` «About the project» rewritten for this project;
  the donor's stale claims fixed against the code: six modules (not one), SQLite default,
  and «SPA served by nginx, never by the backend» corrected to `mount_spa` (the backend serves
  `web/dist` itself). Dead `dev/docs/*` links repointed; `--module=core_users` → `web_search`.
- **Memory (5)** — router line, archive, dev-query/browser/Miro notes.
- **Tasks + plans (21)** — historical records keep their meaning; names, donor paths, the leaked
  dev password and fixture credentials are gone.
- **Code/config (18)** — package name, `web/package.json`, FastAPI `title` → `Uroboros.Research`,
  `.env` + both examples (DB names), `.gitignore`, ten `dev/.run/*.xml`, a bench docstring, test
  fixture emails, three design-system demo strings + the same literals in the committed bundle
  chunks (pnpm is absent, so no rebuild was possible; vendor syntax-grammar chunks left alone).

`uv.lock` still carried the old virtual-root package name, which desynced it from the renamed
`pyproject.toml` and broke **every** `uv run` (uv tried to re-resolve; this environment has no
network, so `uv lock` could not fix it). Edited that single identity field by hand — `uv run`
verified working again afterwards.

Tests: `.venv/bin/pytest -q` → **446 passed**.

### Left for the user

- **PyCharm**: `dev/.run/*.run.xml` now reference module `urb_research` and SDK `uv (urb-research)`
  — rename the IDE module and interpreter to match, or the run configs won't resolve.
- **`web/dist`**: rebuild with `pnpm --dir web build` once pnpm is available (bundle literals were
  patched in place; chunk hashes are unchanged, which is harmless but not pristine).
- **`uv lock`**: re-run it when there is network, to regenerate the lock properly.

### Deliberately not touched

`asyncio.Semaphore` and every `semaphore`/`_semaphore` identifier — a concurrency primitive, not
the donor's name.

### Adjacent staleness found, not in scope (needs a separate pass)

- Dead `dev/docs/` links remain in `docs/workflow/debugging.md`, `docs/platform/architecture.md`,
  `docs/platform/router.md`.
- `docs/INDEX.md` + `docs/mcp/INDEX.md` + `docs/platform/router.md` still claim «no registered
  module currently ships an MCP server» — `research` ships 23 tools.
- `agent-primary.md` Testing section claims `heavy` is Postgres-only because migrations use
  `postgresql.*` types; migrations were since moved to portable types.
- Memory still describes cut functionality (SPA login, `/me` bootstrap, `user-profile`,
  `core_users`): `dev_browser_login.md`, `frontend_auth_bootstrap.md`, `user_profile_feature.md`
  are candidates for deletion or archival.
