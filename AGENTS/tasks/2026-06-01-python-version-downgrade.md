---
title: Downgrade required Python to 3.12
date: 2026-06-01
status: completed
description: "Another dev's `uv sync --all-groups` failed — uv could not find/download Python 3.14.4. Lowered the project's required Python to 3.12."
tags: [build, tooling, python]
---

## Task

"давай понизим версию под 3.12 выбери и пропиши" — у другого разработчика
`uv sync --all-groups` падает с `No interpreter found for Python 3.14.4 in
managed installations or search path`.

## Context

`pyproject.toml` requested `requires-python = ">=3.14.4"` and `.python-version`
pinned `3.14.4`. That interpreter is not installed on the other dev's machine
and his uv is too old to download it. 3.12 is widely available (3.12.3 ships in
the system path) and was chosen as the floor.

## What was done

- `pyproject.toml`: `requires-python = ">=3.14.4"` → `">=3.12"`.
- `.python-version`: `3.14.4` → `3.12`.
- Verified no other version pins (ruff/mypy target, classifiers, CI) — only
  bench `tmp/` artifacts mention 3.14, irrelevant.
- Re-ran `uv sync --all-groups` (re-resolved on 3.12.3, lockfile updated).
- Sanity: `uv run python --version` → 3.12.3; imported fastapi/sqlalchemy/
  pydantic/PySide6 OK.

## Result

Changed: `pyproject.toml`, `.python-version`, `uv.lock`. Project now runs on
Python 3.12; the other dev can `uv sync` without downloading 3.14.
