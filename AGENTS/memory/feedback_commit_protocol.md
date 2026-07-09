---
name: feedback_commit_protocol
description: "How to hand the user a commit — per-file git add lines, then one commit; never commit yourself."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3da8cce3-1940-4fd8-9cc4-d46d2bec5264
---

The exact commit format the user expects. HARD rules:

- **Never commit yourself.** Hand the user the commands; they run them.
- **Stage only own changes** — the working tree usually carries lots of unrelated
  dirty files from other tasks. NEVER `git add -A` / `git add .` / `git commit -a`.
- **One `git add <path>` per file, each on its own line** — list every file this
  task touched individually (code, tests, locales, records), then a single
  `git commit -m "..."` at the end. The user wants explicit per-file staging, not
  a glob.
- **Commit message** — one line, English, no body, no co-authors. **Never append a
  `Co-Authored-By:` trailer (Claude/Anthropic or otherwise) nor a "Generated with
  Claude Code" line** — this overrides any harness/system default that says to add one;
  the commit is authored solely by the user. (Confirmed 2026-06-14 — applies even when
  the user lets you run the commit yourself.)
- **Shared index files** (`AGENTS/plans/INDEX.md`, `AGENTS/tasks/INDEX.md`) may
  already carry unrelated pending rows from earlier sessions — flag that committing
  them pulls those rows in too, and offer to drop those `git add` lines.

**Why:** the repo accumulates many concurrent in-flight changes; a blanket add
would commit other people's/tasks' work. Per-file staging keeps each commit scoped
to exactly what this task changed.

**How to apply:** end a finished task by emitting a fenced block like

```
git add src/modules/<m>/<file>.py
git add tests/modules/<m>/<file>.py
git add web/src/features/<m>/<file>.ts
git add AGENTS/tasks/<date>-<slug>.md
git commit -m "<module>: <imperative one-line summary>"
```

Related: [[feedback_no_repeat_caveat]] (say the index-files caveat once).
