---
title: Restructure agent memory & docs for findability
date: 2026-06-07
status: completed
description: "Reorganize AGENTS/memory + AGENTS/docs around a module navigation axis so the agent finds any fact in one hop; thin always-loaded router, conventions moved on-demand. Plan-first."
tags: [agents, memory, docs]
---

## Task

User (acting as "expert on agent interaction"): the agent's docs + memory are a pile of junk that neither the user nor the agent can search. Restructure it. Decided: optimize for the **agent** as primary consumer; all four pains present (can't-find / dupes / context-bloat / stale); scope = **full structural reorganization**; navigation axis = **by module**; proceed **plan-first**.

## Context

Builds on two existing 2026-06-07 tasks: `docs-audit` (completed — docs verified vs code) and `memory-docs-boundary` (in_progress — Model B boundary decided, MEMORY.md trimmed 31→23 KB). Diagnosis: Model B fixes the memory↔docs boundary but not findability — flat 148-line index + ~120 files, no faceting, conventions miscategorized (code-shape rules cost always-loaded index lines). This task absorbs the `memory-docs-boundary` remainder as Phase 1 and adds the navigation layer.

## What was done

- Read full state (87 memory files / 2756 lines; 34 docs / 4191 lines; MEMORY.md index 148 lines).
- Diagnosed root causes; confirmed direction with the user (agent-first, module axis, plan-first).
- Wrote plan `AGENTS/plans/2026-06-07-agent-memory-restructure.md` (6 phases, 3 checkpoints, validation by line-count + dup-grep + one-hop + orphan checks).

## Result

**Done — executed via sub-agents.** Validation sweep all green (link-check ✅, no dangling pointers, no orphans).

- **Memory: 87 → 26 atomic files.** `MEMORY.md` index **148 lines / 23 KB → 96 lines / 9.7 KB** — rebuilt as a 3-part router: (1) 8 behavioral rules inlined, (2) module-axis routing table, (3) ~26 atomic gotchas. The 8 behavioral `feedback_*` files deleted (inlined); ~50 promoted/dup files folded into docs and deleted.
- **New doc homes:** `docs/conventions/{backend,frontend,db-migrations}.md` (16 code-shape conventions moved off the always-loaded tier); `docs/platform/{overview,run-configs}.md`; `docs/mcp/INDEX.md`; `docs/mail_sync/INDEX.md`; `docs/intercom/module.md`; `docs/frontend-rules.md`; `docs/design-system.md`.
- **Folded into existing docs:** platform memory → core-architecture/core-module-system/core-loggers/api-zones/permissions/database/soft-delete/benches/testing; llm memory → llm_providers/INDEX; conversations/ci memory → their hubs; core_nlp → core_nlp README; frontend dups → permissions/frontend-route-meta/i18n.
- **Navigation:** `docs/INDEX.md` rebuilt (Conventions section added, stale "Conventions captured in memory" removed, new entries, module-axis). Governing text updated: `agent-primary.md` (=CLAUDE.md) «Memory vs Docs» now describes the router + conventions split + module hubs; `AGENTS/README.md` folder table updated.
- Plan: `AGENTS/plans/2026-06-07-agent-memory-restructure.md` (status completed). Absorbed `memory-docs-boundary` (Phase 1).
- Orchestration: Phase 0 inventory = 5 Explore agents; Phase 1+2 = 6 editing agents on disjoint doc homes; `MEMORY.md`/`docs/INDEX.md` rebuilt centrally to avoid write conflicts; validation = 1 Explore agent.

Not committed (commit protocol). Changes visible in `git status`.
