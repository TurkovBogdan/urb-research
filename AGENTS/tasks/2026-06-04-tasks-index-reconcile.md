---
title: Tasks INDEX reconcile — move closed rows to Completed
date: 2026-06-04
status: completed
description: "Audit the In work table against each task file's frontmatter status; move every finished row to Completed and flip status on the ones whose work shipped but status was never updated."
tags: [housekeeping, tasks]
---

## Task

User: «Проверяем все текущие активные задачи, нужно понять что из них уже закрыто» → then «давай» to clean up the index.

## Context

The "In work" table had drifted: many rows carried `**completed**` prose but were never moved to the "Completed" table, and several rows whose work had clearly shipped still had `status: in-work` in their frontmatter (status never flipped).

## What was done

- Read every In-work task file's frontmatter `status` (source of truth) and reconciled it against the index prose.
- Flipped `status: in-work`/`in_work` → `completed` on 9 files whose `## Result` shows shipped work but status was stale: volume-report, twenty-i18n, core-geo-fixed-header-tables, tasks-ui-runs-detail, conversation-insights-reports, conversation-insights-frontend, conversation-insights-module, conversations-module, conversation-insights-agent.
- Moved 42 finished rows from "In work" to the top of "Completed" in `INDEX.md` (32 already `completed` + the 9 above + `route-loading-bar`).
- Kept 8 genuinely-open rows in "In work": worker-split-config (Part 2/3 deferred), api-zones (api/webhook zones pending), usb-conversations-mcp-oversized-output (investigation only), import-full-vs-update-checkpoint (idea), twenty-bench-entities (Result TBD), core-geo-business-data (cg03/cg04 pending), lmstudio-integration (incremental), llm-providers-mcp-servers (runtime-sync/seeder/tool-loop deferred).

## Result

- `AGENTS/tasks/INDEX.md`: In work 50 → 8 rows; Completed grew by 42.
- 9 task files: `status` flipped to `completed`.
