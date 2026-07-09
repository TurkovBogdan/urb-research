---
title: Architecture & purpose review — research MCP is the product core
date: 2026-07-04
status: completed  # in-work | completed | deferred
description: "Debrief/alignment on what the project is FOR: the research MCP server is the product core; the web server is an auxiliary layer for configuration and viewing/debugging research. Identifies the MCP-surface gap and records the MCP-auth direction. Review-only, no code."
tags: [architecture, mcp, research, purpose]
---

## Task

«Давай разберёмся с архитектурой и предназначением. Весь этот проект в первую
очередь должен обеспечить пользователя MCP для проведения ресёча. Вебсервер тут
приятный бонус для настройки проекта и просмотра исследований/отладки.» —
разбор полётов, не реализация.

## Purpose (aligned)

Product = **research MCP server** (+ central "memory block" of knowledge artifacts
reusable across projects). The web server is auxiliary: configuration
(`/core/settings`, ENV via `core_setup`) + viewing/debugging research
(`web_content` viewer, `core_monitoring`).

Layer stack by importance:
- MCP surface (`/mcp/<code>`) — **product core, but no module ships one yet**.
- Research pipeline — designed (obsidian), not coded; prototype in `../urb-mcp-research`.
- `web_content` — Layer 1, raw documents (search + fetch + markdown, url-hash dedup) = root of the design's `document` cache.
- `core_gateway` — external-API boundary (Tavily/Firecrawl + keys); research engines will sit under it.
- `core_setup` / `core_monitoring` — web-layer infra.

## Findings (the gap)

1. **No MCP server exposed.** Core infra (`src/core/mcp/`, `mount_mcp_servers`) is
   built + tested, but every module's `Module.mcp_servers` is empty. The product
   whose "main thing is MCP" does not yet serve MCP.
2. **MCP-auth blocker in the no-auth build.** `mount_mcp_servers` →
   `_collect_resolver` requires **exactly one** `mcp_token_resolver` (was supplied
   by the now-stripped auth module). As soon as a module declares an MCP server,
   boot raises `RuntimeError`. Must be resolved before the first MCP server mounts.
3. **Pipeline not ported.** Prototype `../urb-mcp-research` (stateless, disk
   artifacts) does the full cycle: `query → plan subqueries → search (Tavily→DDG)
   → scrape → chunk → embed-filter (e5-large daemon, GPU) → Grok report`. This
   project has only `search+fetch` (`web_content`). Missing: subquery planning,
   chunking, embedding filter, report synthesis, and the cache/audit tables
   (10-table schema in `obsidian/tables.canvas`).

## Decision recorded

**MCP-auth direction (AskUserQuestion, 2026-07-04):** add a static **token to the
core ENV settings** (via the `core_setup` allowlist). Core itself supplies a
resolver that checks this single ENV token as a Bearer, unblocking
`_collect_resolver` without re-adding a full auth module. Implement when the first
MCP server lands.

**"Research home" (module vs web_content) — deferred:** user chose "just a debrief
for now", so the module boundary for the research pipeline / MCP server is NOT
fixed yet. Open thread continues in `2026-06-27-research-pipeline-design`.

## Result

Review-only, no code. Alignment captured here + memory router note.
Open threads: research pipeline home + design detail
(`2026-06-27-research-pipeline-design`); MCP-auth ENV token (this file).
