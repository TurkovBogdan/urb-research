---
title: Prune task log of deleted-module tasks + empty archive
date: 2026-06-27
status: completed
description: "Post-module-strip cleanup of AGENTS/tasks: delete every task tied to a removed module (now a different project — research MCP), empty the archive, rebuild INDEX.md from the kept rows."
tags: [tasks, maintenance, cleanup]
---

## Task

«Удали задачи связанные с удалёнными модулями, это уже другой проект. И очисти архив.»

Decisions (AskUserQuestion, 2026-06-27):
- Archive → **empty entirely** (clean slate; `archive/INDEX.md` removed too).
- UI tasks → **delete those tied to deleted modules** (chat/message/feature views for
  conversations/intercom/mail), **keep** generic frontend shell + design-system.

## What was done

- Classified all root task files against the deleted-module set (mail_sync, intercom,
  conversations, conversation_insights, twenty, content_parser, llm_providers,
  user_contacts, team, core_geo, core_security, core_monitoring, core_storage,
  core_users/auth, core_mcp).
- Deleted **256** root task files (deleted-module + module-tied UI) and **emptied the
  archive** (61 files incl. its INDEX).
- Kept **65** task files: core/platform, build/server/deploy, dev infra, agent infra
  (memory/docs/tasks/commit), generic frontend shell + design-system, the two strip tasks,
  and the new project's `2026-06-27-research-pipeline-design.md`.
- Rebuilt `INDEX.md` from the kept rows: 2 in-work + 53 completed, empty Deferred,
  Archive note updated. No dangling links.

## Problems

- One row was a false match (a deleted mail-sync row mentioned a kept task inline) — caught
  by the dangling-link check and dropped (filter rows by their own first link).
- No git repo is reachable from this path → deletions are **not** git-recoverable. Done
  under explicit user authorization.

## Result

- `AGENTS/tasks`: 65 task files, archive empty, INDEX clean (no broken links).
- One judgment call: `2026-06-04-dev-slow-requests-diagnosis.md` (old-project dev
  diagnosis) was deleted with the rest; flag for the user.
- 10 kept files have no INDEX row — pre-existing gap (absent in HEAD too), not introduced.
