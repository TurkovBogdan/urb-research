---
title: Module description field
date: 2026-07-05
status: completed
description: "Add a human-readable `description` ClassVar to the base Module contract, set it on all 6 modules, and surface it on the settings page card."
tags: [core, module, settings]
---

## Task

«давай добавим кроме названия поле описания на уровне всех модулей» — add a `description`
field alongside `name` at the base `Module` level. Scope (user-picked): contract + surface
in UI; prose `description` only (no separate `title` — human label stays in `MODULE_LABELS`).

## Context

`Module` exposed only `name` (tech code, e.g. `web_search`). The settings page shows module
cards labelled via a hardcoded frontend `MODULE_LABELS` map; there was no backend-owned prose
about what each module does.

## What was done

- `src/core/module.py` — added `description: ClassVar[str] = ""` to base `Module` (next to `name`).
- Set `description` (Russian prose) on all 6 concrete modules:
  - `web_search`, `core_gateway`, `core_setup` (also annotated `name: ClassVar[str]` + `from typing import ClassVar`), `core_monitoring`, `core_mcp`, `research_registry`.
- `src/core/settings/registry.py` — new `description(module)` accessor reading the stored module instance (`self._modules`).
- `src/core/settings/api.py` — `_module_payload` now includes `"description"` from the registry.
- `web/src/features/settings/api.ts` — `ModulePayload` gains `description: string`.
- `web/src/features/settings/views/SettingsView.vue` — renders `VCardSubtitle` with `m.description` under the title.

Note: surfacing only shows for settings-bearing modules (those in the registry: `core_gateway`,
`web_search`) since the settings page lists only modules with a `settings_schema`.

No tests added — existing `tests/core/settings` (49) cover the payload shape and pass unchanged.

## Result

Backend contract carries per-module prose; settings cards show it. Changed: `src/core/module.py`,
`src/modules/{web_search,core_gateway,core_setup,core_monitoring,core_mcp,research_registry}/module.py`,
`src/core/settings/registry.py`, `src/core/settings/api.py`, `web/src/features/settings/api.ts`,
`web/src/features/settings/views/SettingsView.vue`. `pytest tests/core/settings` 49 passed.
`web/dist` not rebuilt (no pnpm on PATH).
