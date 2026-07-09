---
title: Commit agent layer to git via AI-AGENTS snapshot
date: 2026-05-31
status: completed
description: "AGENTS/AGENTS.md/CLAUDE.md are git-ignored symlinks into an external store; commit a real-file copy as AI-AGENTS/ refreshed by a sync script, documented for fresh clones."
tags: [repo, agents, git]
---

## Task

Agent files (`AGENTS/`, `AGENTS.md`, `CLAUDE.md`) are symlinks into an external agent store, so git would store dangling symlinks. User wanted the agent layer committed as real files — without the inversion approach (repo-as-canonical). Chosen scheme: git-ignore the symlinks, commit a real-file copy `AI-AGENTS/` produced by a sync script, document materialization in a fresh clone.

## What was done

- `.gitignore`: ignore `/AGENTS`, `/AGENTS.md`, `/CLAUDE.md` (under the existing `# agents` block).
- `sync-ai-agents.sh` (repo root, committed): `rm -rf AI-AGENTS && cp -rL AGENTS AI-AGENTS` — dereferences symlinks to real files. Verified: 223 files, no nested symlinks.
- `AI-AGENTS/` generated and confirmed not git-ignored; symlinks confirmed ignored.
- `AGENTS/README.md`: added "Git layout: AI-AGENTS vs AGENTS" — maintainer refresh (`./sync-ai-agents.sh`) + fresh-clone materialization (`cp -r AI-AGENTS AGENTS`, then copy/symlink `agent-primary.md` → `CLAUDE.md`/`AGENTS.md`).
- Root `README.md` structure group "Для AI-агентов" now shows `AI-AGENTS/` as the only git-tracked copy, linking `AI-AGENTS/README.md`.

## Result

New: `sync-ai-agents.sh`, `AI-AGENTS/` (committed snapshot). Edited: `.gitignore`, `AGENTS/README.md`, root `README.md`. AI-AGENTS must be refreshed via the script after agent-layer edits.
