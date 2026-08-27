---
title: Import dev DB from the stable instance
date: 2026-08-26
status: completed
description: "Bring the live dev SQLite database over from the sibling checkout /mnt/store-dev/agents/mcp/urb-research-stable into this working copy, so the accumulated research data can be worked on here."
tags: [database, runtime]
---

## Task

«Перенеси базу из `/mnt/store-dev/agents/mcp/urb-research-stable/` — там куча косяков, будем решать.»

## Context

The stable checkout runs a live backend (`src/app.py`, port 22020) plus a fleet of `--mcp-stdio`
shim processes, and holds the real accumulated data. This working copy's dev DB was a stale
snapshot from 2026-07-09 (20.7 MB vs 38.8 MB).

Both DBs are SQLite, `journal_mode=delete` (no WAL sidecars), and — checked before copying —
carry **identical Alembic heads** (`com_005_modules_state` / `wsm_003_result` /
`rem_005_source_document`) and an identical `core_modules_settings` key set, so no schema
reconciliation was needed.

## What was done

- Compared both DBs read-only: table list + row counts, Alembic heads, settings keys, journal mode.
- Confirmed no backend of *this* checkout is running (nothing on `:12200`) → no deleted-inode risk.
- Backed up the existing dev DB → `runtime/dev/app.sqlite3.bak-20260826-213822` (20.7 MB, kept).
- Copied via the **SQLite backup API** from a read-only connection, not `cp` — the source DB is
  being written to by the live stable backend, so a byte copy could catch a torn transaction.
- Verified the snapshot: `PRAGMA integrity_check` → ok, `PRAGMA foreign_key_check` → ok, row counts
  match the source.
- Moved it into place and ran `migrate check` → **up to date, nothing to apply**.

## Problems

`uv run` broke mid-task: `pyproject.toml` had just been renamed to `urb_research`
by the donor-purge work while `uv.lock` still carries the old virtual-root name, so uv tries to
re-resolve — and there is no network in this environment (`pypi.org` DNS failure). Worked around by
calling `.venv/bin/python` directly. `uv.lock` needs the root package name fixed (a plain `uv lock`
will fail offline) — tracked in [2026-08-26-purge-donor-project-traces.md](2026-08-26-purge-donor-project-traces.md).

## Result

`runtime/dev/app.sqlite3` (38.8 MB) now holds the stable instance's data as of 2026-08-26 21:38:

| Table | Rows |
|---|---|
| research_index | 40 |
| research_area | 291 |
| research_note | 231 |
| research_source_query | 1059 |
| research_source_document | 5311 (kept 3268 / filtered 1954 / pending 89) |
| web_search_query | 1168 |
| web_search_page | 4331 |
| web_search_query_result | 5893 |
| core_modules_settings | 20 (connector API keys carried over) |

Note: the stable instance is still running and still writing to **its own** DB — this is a
point-in-time snapshot, not a link. Anything done there after 21:38 will not appear here.
