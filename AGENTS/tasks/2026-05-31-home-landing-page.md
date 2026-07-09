---
title: Home / welcome landing page outside modules
date: 2026-05-31
status: completed
description: "Standalone welcome page at /home describing the platform; root redirects to it; clickable sidebar logo navigates to it. Full ru/en i18n."
tags: [frontend, router, i18n, layout]
---

## Task

Create a home page outside the modules with a welcome message and a short intro
about what the platform is. Redirect the root to it. Add i18n support. Clicking
the logo / project name navigates to this page.

## Context

`web/src/router/index.ts` redirected `/` → `/hh/vacancies`, a path with no
matching route (no `hh` feature exists) → broken landing. A stub `views/HomeView.vue`
existed but was unused. The MCP servers' `instructions` text frames the platform as
"the semaphore-core system for running a company through AI agents" — used as the
basis for the welcome copy.

## What was done

- `web/src/views/HomeView.vue` — rewrote the stub into a welcome page: hero
  (◈ glyph + title + lead) + 4 capability cards (module system, scheduler,
  LLM providers, agent infrastructure) + a navigation hint. All strings via `useI18n`.
- `web/src/locales/ru.json` + `en.json` — added a global `home.*` namespace
  (title, lead, hint, capabilities.{modules,scheduler,llm,agents}.{title,text}).
- `web/src/router/index.ts` — `/` now redirects to `/home`; added a `/home` route
  rendering `HomeView` with `meta.scroll: 'y'`.
- `web/src/layout/components/AppSidebar.vue` — wrapped the logo glyph + "Semaphore.Core"
  text in a `<button class="logo-link">` that does `router.push('/home')`; scoped
  styles reset the button to behave like the previous inline flex items.

No tests (frontend-only, no test harness for Vue views here). `vue-tsc --noEmit` passes.

## Result

Visiting `/` lands on the welcome page; the sidebar logo is a working home link;
copy switches with the RU/EN locale toggle. Changed files: the four listed above.

## Update 2026-07-09 — rewrite + redesign for the actual project

The original copy still described the generic "platform core for running a company
through AI agents" (inherited `core_semaphore` framing), which no longer matches this
project — an **experimental MCP server for research with long-term memory** over
researches, documents and a web UI.

- `web/src/locales/ru.json` — rewrote `home.*`: new `badge` ("Экспериментальный
  проект"), `title` = "Uroboros.Research", research-focused `lead`/`hint`, a new
  `flow.*` (research → area → query → source → note pipeline), 4 reframed
  `capabilities` (`mcp`/`search`/`structure`/`result`), and an `entries.*` quick-nav
  block (research / web_search / mcp / connectors).
- `web/src/views/HomeView.vue` — redesigned: hero with pill badge + brand row,
  a horizontal flow strip (icons + arrows) showing the research pipeline, the 4
  capability cards (hover-highlight), and a row of clickable entry buttons that
  `router.push` to the main sections. Icons swapped to domain-relevant Tabler ones
  (Telescope/WorldSearch/ServerBolt/Sitemap/Notes/ArrowNarrowRight/PlugConnected).
  Styling uses existing CSS tokens (`--accent`, `--surface`, `--border-soft`, …).

`vue-tsc --noEmit` passes (exit 0); `ru.json` validates. Frontend-only, no tests.
`web/dist` not rebuilt (dev serves via Vite); a prod build is needed before deploy.
