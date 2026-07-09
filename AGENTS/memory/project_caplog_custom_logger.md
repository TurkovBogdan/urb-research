---
name: project-caplog-custom-logger
description: "pytest caplog can't capture project logs — custom LoggerStore loggers have propagate=False; monkeypatch the module _log instead"
metadata: 
  node_type: memory
  type: project
  originSessionId: 33cceac0-284e-4c78-a170-cdae9b794e99
---

`get_logger()` returns a proxy over `LoggerStore` → stdlib loggers named `core.<channel>` with `propagate=False` (`src/core/loggers/core_logger.py`), so pytest `caplog` never sees them. To assert on log output in tests, monkeypatch the module-level `_log` with a stub that records calls. Also: `googleapiclient.errors.HttpError(None, …)` cannot be constructed (ctor dereferences `resp.reason`) — use a non-HttpError exception to exercise resp-less guard branches.
