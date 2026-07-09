---
name: dead_deps_pruned
description: Dependencies removed 2026-06-05 as dead weight after the headless migration / nh3 swap; memory-footprint cleanup
metadata: 
  node_type: memory
  type: project
  originSessionId: f16ec4f3-9b7f-4e23-ae92-71f00e357bd5
---

Pruned from `pyproject.toml` dependencies on 2026-06-05 (memory-footprint task) — all had **zero importers** in `src/`:

- **PySide6 + qasync** — dead since the headless migration (no `src/gui`, no Qt entry point; the only `qasync` mention left is a comment in `llm_providers/api.py`). PySide6 alone was **642 MB** on disk.
- **lxml** — was pruned (no direct src importer; nh3 replaced it on the mail path, every `BeautifulSoup(...)` passes `"html.parser"`). **Back as of 2026-06-13** as a transitive dep of `pikepdf` (core_storage PDF validator) — bs4 may again eagerly load `bs4/builder/_lxml.py`; still keep passing `"html.parser"` explicitly. Do not list lxml as a direct dep.
- **pymorphy3** — removed with the dead `core_nlp/morph.py` (see [[project_core_nlp_module]]).
- **aiofiles, parsel, inscriptis, dateparser** — never imported anywhere.

`uv sync` dropped 22 packages total (incl. transitive pytz/regex/requests/urllib3/w3lib/cssselect…); `.venv` ~800 MB → 143 MB. Process RSS floor 158 → 132 MB across two cleanups.

`python-dotenv` was KEPT — used by `tests/conftest.py` + `dev/bench/*` (not `src/`).

**How to apply:** before re-adding any of these, confirm a real importer. Don't put eager dictionary/model/SDK loads in `Module.configure()` — it runs in every process incl. web-only ([[project_core_nlp_module]], lazy-loading education page).
