---
name: coverage_greenlet_concurrency
description: "pytest-cov under-reports unless concurrency=greenlet — SQLAlchemy-async code runs in spawned greenlets coverage won't trace by default"
metadata: 
  node_type: memory
  type: project
  originSessionId: 45a23386-0b09-4371-a53f-3b2b89b88242
---

`pytest-cov` silently under-reports coverage of any code touching the async DB: the route/CRUD bodies run inside SQLAlchemy-async **spawned greenlets**, and `sys.settrace` (coverage's default) does not follow into them. Symptom: a handler hit by dozens of tests still shows as "missing".

**Fix:** pass a cov config with `[run] concurrency = greenlet,thread`:
```
uv run pytest --module=<m> -n0 --cov=src.modules.<m> --cov-config=<cfg> --cov-report=term-missing
```
Also: `pytest-cov` is incompatible with `pytest-xdist` here (`'Central' object has no attribute 'configure_node'`) — always add `-n0` for coverage runs. No `[tool.coverage]` section exists in `pyproject.toml`, so the concurrency setting must be supplied explicitly each run.

**Why:** without this you "prove" 89% when the real figure (or the real gap) is different — false confidence about untested branches. **How to apply:** any time you measure module coverage, use `-n0` + a greenlet-concurrency cov config; never trust a bare `--cov` number for DB-backed code.
