---
name: src/ shadows top-level SDK packages under pytest
description: pyproject `pythonpath = ["src"]` makes `src/<name>/` shadow any installed third-party package with the same top-level name; avoid `src/<sdk_name>/` directories.
type: project
originSessionId: 53ceaeb7-0050-4cd9-8948-032e9aa06dfa
---
`pyproject.toml`: `[tool.pytest.ini_options] pythonpath = ["src"]`. Under pytest `src/` is at the start of `sys.path`, so **any directory `src/<name>/`** shadows an installed package with the same name.

Real case (2026-05-16): `src/mcp/` (internal MCP server hh-my-profile) shadowed the official `mcp` SDK → `from mcp import ClientSession` failed in tests. The latent bug existed for a long time: `src/mcp/server.py` itself does `from mcp.server.fastmcp import FastMCP` — this only worked when launched via `run_mcp.py` with project-root in `sys.path`, but failed under pytest with `ModuleNotFoundError: 'mcp.server' is not a package`. Renamed to `src/mcp_server/`.

**Why:** one of those "invisible" bugs that only manifests when a dependency with a conflicting name is added; not immediately obvious to diagnose.

**How to apply:** never name a directory `src/<top-level-name>/` the same as an existing or expected Python package in `pyproject.toml`. For internal services add a suffix (`_server`, `_client`, `_app`). If you see a strange `ImportError` under pytest for an installed package — first suspect: `ls src/<name>/`.
