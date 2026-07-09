---
title: Per-process memory footprint reduction
date: 2026-06-05
status: in-work
description: "Each running process consumes ~160–200 MB RSS; reduce it, especially for web-only processes that load LLM/NLP libs they never use."
tags: [perf, memory, llm_providers, core_nlp, deploy]
---

## Task

User: проект потребляет ~200 MB на каждый экземпляр (процесс), нужно уменьшать.

## Context

Prod runs several web processes (`SERVER_PROCESSES`) + a separate worker. Every
process imports `build_modules()` = all 11 modules with all third-party libs.
Headless server entry is `src/app.py` (CLAUDE.md still describes the old
PyInstaller/Qt desktop — stale).

### Measured (dev, single process RSS via ru_maxrss)

| Stage | RSS | Δ |
|---|---|---|
| baseline python | 36 MB | |
| `build_modules()` (all module imports) | 129 MB | +93 |
| `create_app` (ORM mappers, pydantic, routes) | 158 MB | +29 |
| pymorphy3 dict (first `parse`) | 179 MB | +21 |

Biggest eager third-party imports: anthropic +10, openai +10, mcp +11 (=31 MB),
pymorphy3 dict +21, lxml/bs4/markdownify/mistune ~15.

### Findings

- `llm_providers/module.py` top-level imports pull `client → providers →
  anthropic/openai` and `tools/mcp/manager` → `mcp` eagerly. Web processes never
  call LLM yet pay ~31 MB.
- `core_nlp.configure()` calls `warmup()` (pymorphy3 ~50 MB dict / +21 MB RSS) in
  `create_app`, runs in EVERY process incl. web-only.
- `dateparser`, `inscriptis`, `parsel` are in `pyproject.toml` deps but unused in
  `src/` (install/binary size only, not RSS).

## Candidate levers (per-process saving)

1. Lazy-load LLM SDKs (anthropic/openai/mcp) — import on first provider/MCP use.
   Web saves ~31 MB. Cleanest, largest win.
2. Morphology warmup worker-only (or truly lazy) — web saves ~21 MB.
3. Remove unused deps — install size, not RSS.

Realistic web process: 158 → ~108 MB (−30%), multiplied by process count.

## Corrected measurements (second pass)

Process floor = **158 MB** (build_modules 94 + create_app 28 + python base 36).
The earlier "+21 MB pymorphy" was a MIS-attribution: the OpenCorpora dict is an
mmap'd DAWG, file-backed — `MorphAnalyzer()` + `.parse()` adds only ~1 MB RSS.
**Morphology is NOT a real RSS lever.** Observed ~200 MB = floor + runtime
(conn pools, asyncio, per-request pydantic, glibc arena fragmentation under load).

Per-module import cost (RSS delta):
- core fundament (sqlalchemy/fastapi/pydantic/asyncpg): ~35 MB — irreducible.
- llm_providers: +40 (SDK anthropic+openai+mcp ~31, own code ~9).
- core_nlp: +12 (bs4+lxml+markdownify+mistune) — all consumers are worker pipelines.
- other 9 modules: ~1 MB total.
- create_app: +28 (ORM mappers + pydantic route validators + registration).

Dead code found: `morph.py` (`lemma`/`to_nominative`) has ZERO callers anywhere
(src/tests/dev). `markdown_to_html` also uncalled. `pymorphy3` dep exists only for
the dead morph module.

`MALLOC_ARENA_MAX` has no effect at boot (single-threaded import); it only bites the
runtime gap under concurrent load (24-CPU host → glibc up to 8×ncpu arenas).

## Reserve map (leverage order, prod = several web + worker)

1. Topology / preload-fork (COW) — LARGEST: each web process holds its own 158 MB
   copy; preloading + forking workers shares read-only code pages → host RAM ≈
   158 + N×write-delta instead of N×158. Deploy/run change, no code.
2. Lazy imports (lower the 158 floor, ×N): LLM SDK −31 (parked by user), core_nlp −12.
3. `MALLOC_ARENA_MAX=2` / jemalloc — runtime fragmentation gap; measure on live proc.
4. Cleanup (install size, not RSS): dead morph.py + pymorphy3 dep; unused
   dateparser/inscriptis/parsel.

## What was done

- Investigation + measurement (see tables above). User parked the LLM lazy-load.
- **Removed dead morphology (2026-06-05, on user go-ahead):**
  - deleted `src/modules/core_nlp/morph.py` (`lemma`/`to_nominative`/`warmup` — zero
    callers in src/tests/dev);
  - dropped the `warmup()` call + `configure()` override from `CoreNlpModule`
    (base `configure` is a no-op → class now has no hooks);
  - removed `lemma`/`to_nominative` from `core_nlp/__init__` exports;
  - removed `pymorphy3>=2.0` from `pyproject.toml`; `uv sync --all-groups`
    uninstalled `pymorphy3` + `pymorphy3-dicts-ru` + `dawg2-python`;
  - updated `core_nlp/README.md`, `docs/INDEX.md`, `docs/core-architecture.md`,
    memory (`project_core_nlp_module`, `project_modules_state`, `MEMORY.md`),
    education `lazy-loading.md`.
  - **Effect: process floor 158 → 139 MB (−19 MB) on EVERY process.** The eager
    `warmup()` in `create_app` was the real cost (the isolated mmap measurement had
    mis-attributed it to ~0). Tests: `--module=core_nlp` 171 passed, `--core` 209 passed.

- **Pruned dead dependencies (2026-06-05, same go-ahead):** removed from
  `pyproject.toml` (all zero importers in src) — **PySide6** (642 MB disk, dead since
  headless), **qasync**, **lxml** (nh3 replaced it; bs4 uses stdlib `html.parser`
  everywhere → bs4 stops eager-loading its lxml builder, ≈−4 MB RSS), **aiofiles**,
  **parsel**, **inscriptis**, **dateparser**. `python-dotenv` KEPT (conftest/bench).
  `uv sync` dropped 22 packages incl. transitives; `.venv` ~800 → 143 MB.
  **Floor 139 → 132 MB.** Updated `core_security_module`/`mail_html_security`(stale
  lxml→nh3 index line)/new `dead_deps_pruned` memory. Tests: core_nlp+intercom+
  mail_sync+conversations 855 passed, `--core` 209 passed. See [[dead_deps_pruned]].

## Result

Two cleanups shipped: **process RSS floor 158 → 132 MB (−26 MB)** on every process +
`.venv` ~800 → 143 MB disk. Remaining reserves (see map): topology/COW (largest),
lazy core_nlp (−12) + LLM SDK (−31, parked), allocator tuning. Task stays in-work.
