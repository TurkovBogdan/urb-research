---
title: Tasks/plans maintenance playbook
date: 2026-06-07
status: completed
description: "Create a re-runnable sub-agent playbook that archives aged completed tasks, archives plans whose tasks are done, and harvests loose ends into a code-verified LOST-AND-FOUND.md."
tags: [agents, records, maintenance]
---

## Task

User: we have another task — something like `agent-docs-maintenance.md`, but for keeping `AGENTS/tasks` + `AGENTS/plans` up to date. Clarified scope to three concrete jobs: (1) archive completed tasks once enough time has passed, (2) archive completed plans when all related tasks are done, (3) produce an artifact listing missed/deferred things and report them.

## Context

`agent-docs-maintenance.md` covers memory+docs. Tasks/plans are an append-only historical log, so the lever is archival + loose-end harvesting, not classification/promotion. Decisions taken in discussion (recorded so the playbook reflects them):

- **Age threshold = 14 days**, measured from frontmatter `date` / filename (start date as completion proxy — fine at ~40 tasks/day velocity). NOT git, NOT a new `completed:` field.
- **Plan archive** = plan `completed` AND every related task (by slug + `References`) completed-or-archived; no age gate.
- **Artifact** = single persistent `AGENTS/LOST-AND-FOUND.md`, appended (not overwritten), dedup by `(source + item)`.
- **Loose ends verified against code/git** (fan-out `Explore`): DONE → Resolved, OPEN → kept.
- **Running the playbook = standing authorization to archive** → rewrote the "archiving only at user's request" note in both INDEX files.
- No code-audit of in-work→completed (out of the user's ask); history prose never rewritten.

## What was done

- Created `AGENTS/agent-tasks-maintenance.md` — three jobs, 5-phase pipeline (inventory → archive tasks → archive plans → verify loose ends → reconcile LOST-AND-FOUND + validate), orchestration rules (all shared tables + LOST-AND-FOUND are central write-targets; sub-agents read-only; never rewrite history), code-verification rules, 6-check validation sweep, ready-to-paste prompts, LOST-AND-FOUND.md shape.
- Rewrote the Archive note in `tasks/INDEX.md` + `plans/INDEX.md` to point at the playbook (14-day / all-tasks-done gates; manual request still works).
- Added a "Periodic upkeep" pointer in `agent-primary.md` Tasks section.

## Result

- `AGENTS/agent-tasks-maintenance.md` (new).
- `AGENTS/tasks/INDEX.md`, `AGENTS/plans/INDEX.md` — Archive notes updated.
- `AGENTS/agent-primary.md` — Tasks-section pointer.
- First actual run of the playbook is separate, on the user's command.
</content>
