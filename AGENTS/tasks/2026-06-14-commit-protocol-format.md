---
title: commit protocol — per-file staging format
date: 2026-06-14
status: completed
---

## Request

Pin the exact commit format the user expects: **one `git add <path>` per file**
(never `-A`/`-a`), stage only this task's own changes, then a single one-line
English `git commit`. Record it in memory + AGENTS.md + other AGENTS/ files.

## What was done

- New memory file `feedback_commit_protocol.md` (type=feedback) with the full
  rule + rationale + worked example; MEMORY.md §1 commit-protocol line converted
  to a `[Commit protocol](feedback_commit_protocol.md)` pointer stating the
  per-file-`git add` format.
- `AGENTS/agent-primary.md` (= `AGENTS.md`/`CLAUDE.md` symlink target): added a
  **Commit protocol** rule to Working rules.
- Maintenance playbooks `agent-tasks-maintenance.md` + `agent-docs-maintenance.md`:
  "hand the user a one-line command" → "one `git add <path>` per file + a single
  `git commit`".
- `agent-docs-maintenance.md` classification table: KEEP-ALWAYS destination gained
  an exception so a behavioral rule with rationale/example may keep a `feedback_*`
  file + §1 pointer (browser-isolation, commit-protocol) instead of forced inline —
  prevents a future maintenance run from re-inlining and deleting the new file.

## Problems

- `AGENTS.md`/`CLAUDE.md` are symlinks to `AGENTS/agent-primary.md` — edited the
  real target.

## Result

Done. Commit-protocol format recorded in memory + primary instructions; maintenance
classifier reconciled so the feedback file survives upkeep.
