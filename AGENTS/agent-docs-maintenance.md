# agent-docs-maintenance — knowledge-base cleanup via sub-agents

A runnable playbook for maintaining `AGENTS/memory` + `AGENTS/docs`: dedup, promote, rebuild the
router, fix broken links, and verify every claim against the **current code**. Orchestrated as a
fan-out of sub-agents. Records-only — no `src/`/`web/` changes; safe to run without a go-ahead
(it edits docs/memory, which are records).

**Invoke:** "run agent-docs-maintenance" (full sweep) or name a single phase ("docs-maintenance:
validate only" / "...: code-audit only").

**Worked example:** `tasks/2026-06-07-agent-memory-restructure.md` + `tasks/2026-06-07-docs-audit.md`
+ `plans/2026-06-07-agent-memory-restructure.md`.

---

## 0. The target structure (what we maintain toward)

Defined in `agent-primary.md` → *Memory vs Docs*. In one breath:

- **`memory/MEMORY.md` = a router**, loaded every session, kept small. Three parts only:
  (1) always-apply behavioral rules, (2) routing table `area/module → doc hub`, (3) atomic ≤3-line
  gotchas. No prose, no digests.
- **`docs/` = on-demand reference.** Primary axis = **per-module hubs** `docs/<module>/INDEX.md`
  (mirror `src/modules/`). Cross-cutting homes: `docs/platform/`, `docs/conventions/`, `docs/mcp/`,
  the flat frontend docs, `docs/INDEX.md` (library map).
- **Single home per topic.** Sections/prose → doc. Lone fact → memory. Never both.

Drift this sweep fixes: fat multi-line entries in `MEMORY.md`; the same topic in memory **and** a doc;
mini-docs accumulating in `memory/`; code-shape conventions costing always-loaded budget; stale claims
that no longer match the code; broken/dangling links.

---

## 1. Classification scheme (every memory file lands in exactly one)

| Class | Definition | Destination |
|---|---|---|
| **KEEP-ALWAYS** | behavioral/process rule the agent must obey unprompted (discussion≠go, never-guess, commit protocol, edit-by-hand, re-read, move-with-mv, comment-before-command, commit-English) | inline block in `MEMORY.md` §1 + delete file; **exception** — a rule needing rationale/worked example keeps a `feedback_*` file with a one-line §1 pointer (e.g. browser-isolation, commit-protocol) |
| **CODE-SHAPE** | coding/structure convention, only relevant when touching that code (CRUD/DTO layout, table column order, which Vuetify component, api-url style, versioning axes) | `docs/conventions/{backend,frontend,db-migrations}.md`; delete file |
| **ATOMIC** | sharp ≤3-line gotcha, no prose home | stays a memory file; listed in `MEMORY.md` §3 and/or its module hub |
| **PROMOTE** | multi-section prose | fold into its doc home (existing or new); delete file |
| **DEDUP** | already covered by an existing doc | verify doc covers every fact (add the missing ones), then delete file |
| **REFERENCE** | external-resource pointer (board id, model lineage) | atomic in `MEMORY.md` §3 "Reference" or a reference doc |

Boundary heuristic: **behavioral → memory; code-shape → docs.** This split is the single biggest lever
on always-loaded budget — historically ~25 convention files each cost an index line.

---

## 2. The pipeline (phases + checkpoints)

Run bottom-up so navigation is built on a deduped, code-verified base. Stop and review at each checkpoint.

1. **Phase 0 — Inventory** (read-only fan-out). Classify every `memory/*.md` into the table above
   + target home + `dup_with`. Output a table; collate centrally.
2. **Phase A — Code-actuality audit** (read-only fan-out). Verify doc/memory claims against the
   **current** `src/`/`web/` (see §4). Produce a stale-claims list. *Do this before promotion* so you
   don't fold stale prose into a hub.
3. **Phase 1 — Consolidate** (editing, disjoint homes). PROMOTE + DEDUP: fold prose into doc homes,
   delete the memory file. Kills duplication. **Checkpoint 1:** no topic in both tiers.
4. **Phase 2 — Reclassify conventions** (editing). Move CODE-SHAPE → `docs/conventions/`.
   **Checkpoint 2:** conventions no longer cost individual index lines.
5. **Phase 3 — Rebuild `MEMORY.md`** (CENTRAL, single agent = you). Three-part router; inline the
   KEEP-ALWAYS block; delete those files.
6. **Phase 4 — Module hubs** (editing). Each active module has a `docs/<module>/INDEX.md` that lists
   its docs + its atomic gotchas. Create missing hubs.
7. **Phase 5 — Governing text + validation** (CENTRAL + final fan-out). Update `docs/INDEX.md`,
   `agent-primary.md`, `README.md`. Then run the validation sweep (§5). **Checkpoint 3:** all green.

A lighter run (no restructure) = Phase A + Phase 5 only: audit claims vs code, fix broken links.

---

## 3. Orchestration rules (hard-won — violate these and you corrupt the run)

- **Sub-agents own DISJOINT doc homes.** Partition by area (conventions / platform / frontend /
  workflow / one bucket per `core_*` module). No two agents touch the same file.
- **Never let a sub-agent edit `MEMORY.md` or `docs/INDEX.md`.** They are shared write-targets →
  parallel edits race. Rebuild both **centrally** (Phases 3 & 5). Tell every sub-agent so explicitly.
- **Read-only fan-out** for Phase 0 + A (use `Explore` agents). **Editing fan-out** only on disjoint files.
- **Preserve every fact.** Folding ≠ summarizing-away. Carry the "Why"/"How to apply" lines and code
  examples verbatim. A fact with no clear home → report it, don't drop it.
- **`mv` to relocate whole files**, then Edit only changed lines; never rewrite a file just to move it.
- **Re-read before edit** — docs may be edited live by the user mid-run; cached state goes stale.
- **Edit by hand** — no sed/scripted rewrites.
- **Each sub-agent reports back:** target doc per file, dup-or-new-facts, deletions confirmed,
  facts without a home, and any **discrepancy flagged** (see §4 — never silently "fix" a semantic conflict).
- Scale the fan-out to the work: ~5 inventory + ~6 editing + 1 validation agent covered 87 memory files.

---

## 4. Code-actuality audit (Phase A — the "проверять актуальность коду" requirement)

Docs rot because code moves. A doc that confidently describes deleted code is worse than no doc.
Fan out read-only `Explore` agents, one per doc area, each verifying the doc's concrete claims against
the **current** repo. Check, per doc:

- **Paths/symbols** — every `file.py`, `ClassName`, `function()` referenced still exists (Grep/Glob).
- **DB shape** — table names, column names, PK type, migration prefixes match `models/` + `migrations/`.
- **API** — routes, methods, zone prefixes (`/internal`, `/api`) match the routers.
- **Env/config** — env var names + defaults match `Config`.
- **Module table** — registered modules match `apps/app/modules.py::build_modules`.
- **Counts/versions** — "N tables", "M modules", `PARSER_VERSION`/`AGENT_VERSION`, prices, etc.

Two outcomes, kept distinct:
- **Stale fact** (doc says X, code says Y, no intent conflict) → the audit agent **fixes the doc**.
- **Semantic conflict** (doc states an *intent* the code contradicts — likely a **code bug**, not a
  doc error) → **flag to the user, do NOT auto-edit either side.** Seen before: `i18n.md` says ru-primary
  but code has `fallbackLocale:'en'`; or a memory/doc naming a column, separator, or version the code
  has since renamed. Surface these in the report under "Open items for the user".

Reference run: `tasks/2026-06-07-docs-audit.md` (5 Explore agents, per-doc, hand-verified key claims).

---

## 5. Validation sweep (Phase 5 — must end green)

One read-only `Explore` agent; report `✅ clean` or `❌ file:line` per check. Do NOT fix in the same pass.

1. **Broken links in `MEMORY.md`** — resolve every link (`../docs/…`, `../../src/…`, sibling `*.md`);
   each target must exist.
2. **Broken links in `docs/INDEX.md`** — same, paths relative to `docs/`.
3. **Dangling pointers to deleted files** — grep `docs/**` + `MEMORY.md` for markdown **links** to any
   memory file deleted this run. A prose *mention* of the concept is fine; a **link** to the dead file
   is a bug. (Watch self-referential stale pointers, e.g. a file citing a nonexistent
   `AGENTS/conventions/code-layout.md`; and `[[wikilinks]]` to non-migrated files — drop or fold them.)
4. **Orphan memory files** — every `memory/*.md` (except `MEMORY.md`, `archive.md`) is linked from
   `MEMORY.md`. Orphans = either add to the router or they shouldn't exist.
5. **`MEMORY.md` budget** — report line count + byte size. Hard limit ~24.4 KB (load cutoff); target
   well under (last run landed 96 lines / 9.7 KB, down from 148 / 23 KB).
6. **One-hop test** — sample 5 facts (one per axis); each reachable `MEMORY.md → hub → fact` in ≤1 hop,
   living in exactly one place.
7. **Code-actuality residue** — confirm Phase A's stale list was applied and "Open items for the user"
   are surfaced, not silently resolved.

---

## 6. Ready-to-paste sub-agent prompts

Adapt the file lists to the current `ls memory/`. Base dir: the repo's `AGENTS/`.

**Inventory (Phase 0), per area — `Explore`:**
> Read each of these memory files (AGENTS/memory/) and classify into the §1 scheme. Output one table
> row per file: `| file | line_count | class | target_home | dup_with | one_line_summary |`. To detect
> dups, grep AGENTS/docs for the topic. Return only the table + a 2-3 line findings note. Edit nothing.
> Files: <list>

**Code-actuality audit (Phase A), per doc area — `Explore`:**
> For each doc in <area>, verify its concrete claims against the CURRENT code (paths, symbols, table/
> column names, migration prefixes, routes, env vars, counts/versions) via Grep/Glob/Read. Report, per
> doc: ✅ accurate, or a list of `file:line — claim — reality`. Separate **stale facts** (fix the doc)
> from **semantic conflicts** (doc intent vs code — likely a code bug; flag, don't edit). Apply only the
> stale-fact fixes; list conflicts under "Open items for the user". Do NOT touch MEMORY.md / docs/INDEX.md.

**Consolidation (Phases 1-2), per area — default agent:**
> Records-only; you ARE cleared to edit docs and delete memory files. Fold these memory files into their
> doc home (preserve EVERY fact + Why/How-to-apply + examples), then `rm` the source. <mapping: file →
> target doc/section>. For DEDUP files: first verify the target doc already covers every fact, add any
> missing one, then delete. Match the terse dense doc style. Do NOT touch AGENTS/memory/MEMORY.md or
> AGENTS/docs/INDEX.md (rebuilt centrally). Do NOT touch files not listed. Report: per file — target,
> dup-or-new-facts, deletion confirmed, any fact without a home, any discrepancy flagged.

**Validation (Phase 5) — `Explore`:** the seven checks in §5 verbatim; report `✅`/`❌ file:line`, fix nothing.

---

## 7. Central steps you (the orchestrator) do yourself — never delegate

- **Rebuild `MEMORY.md`** (Phase 3): three-part router; inline KEEP-ALWAYS; delete those files.
- **Rebuild `docs/INDEX.md`** (Phase 5): library map on the module axis; add new homes; remove stale
  "captured in memory" sections.
- **Governing text** (Phase 5): `agent-primary.md` (= `CLAUDE.md` symlink) + `README.md`.
- **Collate** every sub-agent report; act on flagged conflicts; close the task + plan records.
- **Do not commit** (commit protocol — hand the user one `git add <path>` per file + a single `git commit`).

---

## 8. Lessons (from the 2026-06-07 run)

- The convention split (behavioral→memory, code-shape→docs) is what actually shrinks the always-loaded
  tier — do it first among the reclassifications.
- Audit **before** promote: don't fold stale prose into a hub, then have to fix it in two places.
- Disjoint-homes + central rebuild of the two shared indexes is the whole game for parallel safety.
- Semantic conflicts are signal, not noise — they often reveal a code bug. Always surface, never auto-merge.
- Sub-agents drift toward summarizing; insist "preserve every fact" and have them report orphaned facts.
- After the run, the structure is self-documenting in `agent-primary.md` + `README.md` + the indexes —
  do NOT add a memory entry describing it (that would re-bloat the tier this playbook exists to keep thin).
