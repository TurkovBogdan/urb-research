---
name: AppPath.tmp
description: AppPath gained a `tmp` field (`runtime/<profile>/tmp/`) for ephemeral per-run scratch dirs created and cleaned up by tasks
type: project
originSessionId: 686b1434-4a46-441d-965d-d24ed59d898a
---
`src/core/app_path.py` now exposes `AppPath.tmp` alongside `logs`/`cache`/`user`/`import_`.

**Why:** added for a sync task that downloads files to a per-run subfolder and removes them in `finally`. Distinct from `import_/` (which is a stable "import contract" directory) and `cache/` (persistent).

**How to apply:** any task that fetches/produces files purely as intermediate scratch should use `AppPath.from_root().tmp / "<module>" / <unique>` and `shutil.rmtree(..., ignore_errors=True)` in `finally`. `ensure_dirs()` creates the dir on boot.
