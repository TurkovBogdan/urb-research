---
title: Study src/core platform layer
date: 2026-07-02
status: completed
description: "Read-only walkthrough of src/core (all subsystems) to build an up-to-date architectural picture; summary reported in chat. No code changed."
tags: [core, platform, study]
---

## Task

«@src/core изучи» — study the platform core and report its structure.

## Context

Orientation request; no change intended.

## What was done

- Inventoried all `.py` files under `src/core` (~5300 lines) and read the key ones: `app_factory.py`, `module.py`, `config.py`, `settings.py`, `app_path.py`, `router/` (mounting, internal, spa, guards/enforce, mcp), `scheduler/` (registry API, ticker, runner), `database/` (runtime, migrations, types), `locks/lock.py`, `_settings/` (registry, fields), `module_state.py`, `mcp/` (factory, package), `loggers/`, `api/errors.py`.
- Summarized the architecture in chat (Russian): create_app lifecycle, Module contract, HTTP zones + guards, MCP mounting, scheduler/locks, dual-provider DB, runtime settings vs module state, Config env groups.

## Result

Study only — no files changed. Summary delivered in chat.
