---
title: Create agent-docs-maintenance playbook
date: 2026-06-07
status: completed
description: "Capture the memory/docs cleanup operation (run via sub-agents) as a reusable root playbook agent-docs-maintenance.md, incl. broken-link + code-actuality verification."
tags: [agents, docs, memory, playbook]
---

## Task

User: in AGENTS root create `agent-<doc-update>` to launch our cleanup operation using sub-agents; embed all current experience. Must also check broken files AND actuality against code.

## Context

Follows `2026-06-07-agent-memory-restructure` (restructured memory+docs via 5 inventory + 6 editing + 1 validation sub-agents). The user wants that operation captured as a runnable playbook so it can be re-run periodically, adding an explicit code-actuality audit (only implicitly covered last time via the separate `docs-audit` task).

## What was done

- Created `AGENTS/agent-docs-maintenance.md` — phased pipeline, classification scheme, orchestration rules, ready-to-paste sub-agent prompt templates, validation checklist (broken links + orphans + dups + code-actuality), lessons/gotchas.

## Result

- New file: `AGENTS/agent-docs-maintenance.md`.
