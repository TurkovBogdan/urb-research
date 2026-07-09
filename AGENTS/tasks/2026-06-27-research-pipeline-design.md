---
title: Research MCP — pipeline & table design (Obsidian Canvas)
date: 2026-06-27
status: in-work  # in-work | completed | deferred
description: "Design the work pipeline and DB table structure for the research/search MCP server. Capture it as an Obsidian Canvas in AGENTS/obsidian. Design-only — no code yet."
tags: [research, mcp, design]
---

## Task

«Мы создаём mcp сервер для проведения ресёча и поиска, нужно выработать его pipeline работы и структуру таблиц. Работаем в `AGENTS/obsidian`. Создаём схему pipeline в виде схемы обсидиан.»

## Context

A working prototype already exists at `../urb-mcp-research` (stateless: writes per-run artifacts to disk).
Pipeline today: `query → plan subqueries → search (Tavily→DDG) → scrape → chunk → embed-filter → Grok report`.
Tools exposed: `search` (no scrape/LLM) and `research` (full pipeline). Embedding via a separate
`intfloat/multilingual-e5-large` daemon (TCP loopback, ~2.5–3 GB VRAM).

Decisions taken (AskUserQuestion, 2026-06-27):
- **DB role:** cache & reuse — store scraped docs, chunks, embeddings to skip re-scrape / re-embed across runs.
- **Deliverable format:** Obsidian Canvas (`.canvas`).
- **Target code home:** undecided — design-only for now.

## What was done

- Reverse-engineered prototype pipeline + data shapes from `../urb-mcp-research/src`.
- Designed a cache-aware pipeline and a 10-table schema (3 cache tables + run/audit/result tables).
- Authored Obsidian Canvas files in `AGENTS/obsidian/`.

## Result

- `AGENTS/obsidian/00-overview.md` — index + cache strategy notes.
- `AGENTS/obsidian/pipeline.canvas` — runtime flow with cache lookups.
- `AGENTS/obsidian/tables.canvas` — ER / table structure.

## Decisions

- **Module name (2026-07-04):** the orchestrator module is **`research_registry`**
  (AskUserQuestion). Domain module (no `core_` prefix, like `web_content`);
  home `src/modules/research_registry/`; MCP server at `/mcp/research-registry`.
  It owns the registry data model shown in the canvases —
  `Research → Queries → per-query Report → Documents` (relevance + summary on the
  document↔query link) — plus pipeline orchestration. **Consumes** `web_content`
  (search + page content) and `core_gateway` (external APIs); does no network itself.
  MCP-facing surfaces: research registry (start/register/form queries), document
  registry (fetch set / mark relevance / bind summary), per-query report synthesis.
