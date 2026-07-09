# agent-tasks-maintenance — tasks/plans archival + loose-end harvest via sub-agents

A runnable playbook that keeps `AGENTS/tasks` + `AGENTS/plans` lean and honest. It does **three
jobs**: (1) archive completed tasks older than a threshold, (2) archive completed plans whose every
related task is done, (3) harvest loose ends (follow-ups / deferred / TODO) into a persistent
`AGENTS/LOST-AND-FOUND.md`, **verified against the current code**. Records-only — no `src/`/`web/`
changes.

**Running this playbook is the standing authorization to archive** (age- and condition-gated below).
It supersedes the old "archiving only at the user's request" note in both `INDEX.md` files; a manual
archive request still works as an addition.

**Invoke:** "run agent-tasks-maintenance" (all three jobs) or name one ("tasks-maintenance: archive
only" / "...: lost-and-found only").

**Sibling:** `agent-docs-maintenance.md` (memory/docs tier). **Reconcile precedent:**
`tasks/2026-06-04-tasks-index-reconcile.md`.

---

## 0. What it maintains toward

- **`tasks/INDEX.md` + `plans/INDEX.md`** are table routers with sections **In work / Completed /
  Deferred / Archive**. Every file = exactly one row; the row's section equals the file's frontmatter
  `status` (`in-work`/`completed`/`deferred`).
- **Completed work doesn't linger.** Once a task has been `completed` long enough, its row + file
  move to `archive/` so the live index stays short (the project produces up to ~40 tasks/day).
- **Plans trail their tasks.** A plan archives only when it's done *and* the work it planned (its
  tasks) is done — never while a related task is still open.
- **Loose ends are never silently lost.** Every "Follow-up:" / "Open:" / deferred item is harvested
  into `LOST-AND-FOUND.md` and re-checked against code until it's actually resolved.
- **The log is append-only history.** Never rewrite a file's "What was done"/"Result"/"Steps" prose
  to match newer code — only `status`, index rows, and file location are living state.

---

## 1. The three jobs (exact rules)

### Job 1 — Archive aged completed tasks
- **Candidate:** frontmatter `status: completed` **AND** age > **14 days**, where age = `today −
  frontmatter date` (= the `YYYY-MM-DD` in the filename; start date is the proxy for completion —
  fine at this project's velocity). `today` is passed into the run, never `Date.now()`.
- **Never** archive `in-work` or `deferred` tasks (they're open), regardless of age.
- **Action:** `mv` the file → `tasks/archive/`; move its row verbatim from `tasks/INDEX.md`
  *Completed* into `tasks/archive/INDEX.md` (kept newest-date-first); fix the link if needed.

### Job 2 — Archive completed plans whose tasks are done
- **Candidate:** plan `status: completed` **AND** every **related task** is completed-or-archived.
  No age gate.
- **Related tasks** = tasks sharing the plan's slug + tasks named in the plan's `## References`
  ("Related tasks:") + tasks whose body links this plan. A task counts as done if it sits in
  *Completed* **or** in `tasks/archive/`.
- If any related task is still *In work*/*Deferred* → **leave the plan**, and add a
  LOST-AND-FOUND note ("plan X done, task Y still open").
- **Action:** `mv` → `plans/archive/`; move its row from `plans/INDEX.md` *Completed* →
  `plans/archive/INDEX.md`.

### Job 3 — Harvest loose ends → `AGENTS/LOST-AND-FOUND.md` (verified)
- **Single persistent file**, appended/reconciled each run (never overwritten).
- **Harvest sources** across all task/plan bodies *and* both INDEX *Deferred* sections:
  `Follow-up:`, `Open:`, `Open (`, `Open items`, `Open question`, `Deferred`, `Deferred per user`,
  `TODO`, `NB:` loose ends.
- **Verify each item against the current code/git** (§4 fan-out): DONE (landed) vs OPEN (no trace).
- **Reconcile the file:** OPEN items not yet listed → append to *Open*; previously-*Open* items now
  DONE → move to *Resolved*; still-OPEN → bump `last_checked`. **Dedup key = (source file + item
  text)** so re-runs never duplicate.
- **Report** the *Open* set in chat after the run.

---

## 2. Pipeline (phases + checkpoints)

1. **Phase 0 — Inventory** (read-only fan-out, `Explore`). For every `tasks/*.md` + `plans/*.md`:
   `status`, frontmatter date, INDEX section, slug, related-slug, and every loose-end line. Collate
   centrally into three work-lists: archive-task candidates, plan→tasks map, harvested loose ends.
2. **Phase 1 — Archive aged tasks** (CENTRAL = you). Apply Job 1: `mv` + move rows. **Checkpoint 1:**
   no `completed` task older than 14d remains in `tasks/INDEX.md`.
3. **Phase 2 — Archive plans** (CENTRAL). Apply Job 2 using the plan→tasks map (now that tasks may
   have moved to archive). **Checkpoint 2:** every archived plan's tasks are all done; no plan
   archived with an open task.
4. **Phase 3 — Verify loose ends** (read-only fan-out, `Explore`, §4). Each harvested item → DONE /
   OPEN + evidence.
5. **Phase 4 — Reconcile `LOST-AND-FOUND.md` + validate** (CENTRAL + final fan-out). Apply the §1
   reconcile rules; run the validation sweep (§5). **Checkpoint 3:** all green; report Open set.

A lighter run = one named job. "archive only" = Phases 0–2. "lost-and-found only" = Phase 0 (harvest)
+ 3 + 4.

---

## 3. Orchestration rules (violate these and you corrupt the run)

- **All shared tables are CENTRAL write-targets — you edit them, never a sub-agent:**
  `tasks/INDEX.md`, `plans/INDEX.md`, both `archive/INDEX.md`, and `LOST-AND-FOUND.md`. Parallel
  edits race the tables.
- **Sub-agents are read-only** (inventory + verification). The actual `mv` + table edits are done by
  one hand (you).
- **`mv` to relocate, then fix only the link.** Never rewrite a file to move it; never edit its body.
- **Never rewrite history.** No folding/summarizing of "What was done"/"Result" prose — ever.
- **Age basis = frontmatter date, never wall-clock in a sub-script.** `today` is an input to the run.
- **Re-read before edit** — files may be edited live mid-run.
- **Each verification sub-agent reports:** per item — DONE/OPEN, the evidence (path/symbol/commit),
  and a one-line reason. Each inventory sub-agent reports its three work-lists.

---

## 4. Loose-end verification (Phase 3)

Fan out read-only `Explore` agents over the harvested items. Per item, decide **DONE vs OPEN**
against the **current** repo:

- **Files/symbols** the item names ("run migration ci08", "add `guard_token`") — present now
  (Grep/Glob)?
- **Migrations / routes / models / env / config** referenced — landed in `migrations/versions/`,
  routers, `models/`, `Config`?
- **git** — a commit whose message matches the item's slug/intent?
- Items that are inherently un-checkable from code (process/ops notes like "re-import data",
  "ask user") → mark **OPEN — manual**, never auto-resolve.

Outcome feeds the §1 reconcile: DONE → *Resolved*; OPEN → stays/added to *Open*. When uncertain,
default to **OPEN** (a false "resolved" silently drops a real loose end).

---

## 5. Validation sweep (Phase 4 — must end green)

One read-only `Explore` agent; report `✅ clean` or `❌ file:line`. Fix nothing in this pass.

1. **No aged completed left** — no `completed` task with date > 14d still in `tasks/INDEX.md`.
2. **Archive moves are complete** — every file moved this run: not in its old dir, present in
   `archive/`, row gone from the main `INDEX.md`, row present in `archive/INDEX.md` (no orphan/dangle).
3. **No plan archived with an open task** — every plan in `plans/archive/` has all related tasks
   completed/archived.
4. **Section == status** — for remaining rows in both `INDEX.md`, file `status` matches the section.
5. **Links resolve** — every row link in both `INDEX.md` + both `archive/INDEX.md` + every
   `LOST-AND-FOUND.md` source link points at an existing file.
6. **LOST-AND-FOUND integrity** — no duplicate `(source + item)` rows; every *Resolved* item has
   evidence; *Open* count reported.

---

## 6. Ready-to-paste sub-agent prompts

Adapt file lists to the current `ls tasks/` + `ls plans/`. Base dir: the repo's `AGENTS/`. Pass
`today=<YYYY-MM-DD>`.

**Inventory (Phase 0), per tree/date-range — `Explore`:**
> For each file below, read frontmatter (`status`, `date`) + body. Emit one row:
> `| file | status | date | index_section | slug | related_slugs | loose_end_lines |`. For
> `loose_end_lines`, quote every line matching Follow-up:/Open:/Open (/Open items/Open question/
> Deferred/TODO/NB: verbatim with its line number. Return only the table + a 2-3 line note. Edit nothing.
> Files: <list>

**Loose-end verification (Phase 3) — `Explore`:**
> For each loose-end item below (text + source file), decide DONE or OPEN against the CURRENT code:
> the file/symbol/migration/route/env it names exists now (Grep/Glob), or a matching git commit
> landed. Items that can't be checked from code (ops/process/ask-user) → OPEN — manual. When
> uncertain → OPEN. Report per item: `DONE|OPEN — evidence (path/symbol/commit) — one-line reason`.
> Edit nothing. Items: <list>

**Validation (Phase 5) — `Explore`:** the six checks in §5 verbatim; report `✅`/`❌ file:line`, fix nothing.

---

## 7. Central steps you (the orchestrator) do yourself — never delegate

- **Archive moves** (Jobs 1–2): `mv` files; move rows from `INDEX.md` → `archive/INDEX.md`
  (newest-first); fix links.
- **Rebuild/append `LOST-AND-FOUND.md`**: apply the §1 reconcile (Open/Resolved, dedup).
- **Order Phase 2 after Phase 1** so the plan→tasks check sees tasks already moved to archive.
- **Report** the Open loose-end set in chat.
- **Do not commit** (commit protocol — hand the user one `git add <path>` per file + a single `git commit`).

---

## 8. LOST-AND-FOUND.md shape (created on first run)

```
# LOST-AND-FOUND — loose ends from tasks/plans

Follow-ups, deferred items, and TODOs harvested from task/plan bodies, re-verified against the code
each run by agent-tasks-maintenance. Appended, not overwritten. Dedup key = (source + item).

## Open
| Item | Source | First seen | Last checked | Notes |
|------|--------|-----------|--------------|-------|

## Resolved (verified landed in code)
| Item | Source | Resolved on | Evidence |
|------|--------|-------------|----------|
```
</content>
