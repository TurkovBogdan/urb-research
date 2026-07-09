---
title: Commit agent layer directly as AGENTS/ (drop AI-AGENTS snapshot)
date: 2026-06-03
status: completed
description: "The agent layer is now a real, directly-committed AGENTS/ folder. The old AI-AGENTS/ snapshot + sync-ai-agents.sh scheme is retired; docs aligned to the new scheme."
tags: [repo, agents, git, docs]
---

## Task

User renamed the committed snapshot `AI-AGENTS/` to `AGENTS/` so the agent layer
goes straight into the repo. Asked to study the agent-folder docs and bring them
in line with the new scheme.

## Context

Previous scheme (see [2026-05-31-agent-layer-git.md](2026-05-31-agent-layer-git.md)):
`AGENTS/`, `AGENTS.md`, `CLAUDE.md` were git-ignored symlinks into the external
store; only a real-file copy `AI-AGENTS/`, refreshed by `sync-ai-agents.sh`
(`cp -rL`), was committed.

New scheme (from this session's git state):
- `AI-AGENTS/` deleted (staged `D`), role taken by the real `AGENTS/` folder.
- `.gitignore`: dropped `/AGENTS` and `/sync-ai-agents.sh` → `AGENTS/` now commits directly; no snapshot, no sync script.
- Root symlinks `AGENTS.md` / `CLAUDE.md` (→ `AGENTS/agent-primary.md`) stay git-ignored — still created per fresh clone.

Side effect: Claude auto-memory (`~/.claude/.../memory` → symlink → `AGENTS/memory/`)
now writes into a committed folder, so memory content is tracked in git.

## What was done

- `AGENTS/README.md` «Установка»: rewrote the snapshot description — `AGENTS/` is committed directly; only the two root symlinks are ignored and recreated after clone.
- Root `README.md`: doc-table row for the agent layer no longer says «из снимка `AI-AGENTS/`».
- `.gitignore`: fixed the `# agents` comment to describe the direct-commit scheme.

Historical task `2026-05-31-agent-layer-git.md` left untouched (it records the
old scheme as it was); this entry supersedes it.

## Result

Edited: `AGENTS/README.md`, root `README.md`, `.gitignore`. The AI-AGENTS
snapshot + `sync-ai-agents.sh` workflow is retired across the live docs.
