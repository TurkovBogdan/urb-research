---
title: Assess extracting simple-scraper-api into a scraping module
date: 2026-07-01
status: completed
description: "Feasibility of pulling simple-scraper-api (patchright browser scraper) into urb-research src/modules. Decision: too heavy for in-process — keep it a standalone daemon; do not extract."
tags: [web_content, scraper, architecture]
---

## Task

User asked whether the page scraper at an external `simple-scraper-api` project
(masquerades as a real browser, "quite heavy") can be extracted as a scraping module into
`src/modules`.

## Context

`simple-scraper-api` is a standalone FastAPI service: `patchright` (Playwright fork with
anti-detect patches) + Chromium binary + `curl_cffi`, a persistent Chrome profile with an
exclusive `user_data_dir` lock, a semaphore-limited page pool living in `lifespan`, plus
auth (Bearer), SSRF guard and file cache. `POST /api/1.0/scrap` returns raw HTML (`page.content()`).

`web_content` already has the integration seam: `SearchProvider.fetch_page(url) -> str|None`
(markdown), driven by the worker task `fetch_due_pages` → `page_set_content`. Active provider
is a `ChoiceField` in module settings.

## What was done

- Mapped both sides: scraper internals (`main.py`, `src/api.py`, `src/browser/context.py`,
  `src/config.py`, `src/models.py`) and the `web_content` provider seam (`providers/base.py`,
  `firecrawl.py`, `registry.py`, `services/fetcher.py`, `module_settings.py`).
- Identified the three constraints that shape any integration:
  1. Scraper is **fetch-only** (no search) — the current one-provider-does-both model would need
     a `search_provider` / `fetch_provider` split (or a fetch-only backend).
  2. Scraper returns **HTML, not markdown** — needs an HTML→markdown pass (`normalize.py` exists).
  3. It is **heavy**: patchright + Chromium binary + exclusive persistent-profile lock, browser
     must live in the worker process, can't share one profile across >1 worker. Reverses the
     project's lean-deps course (`.venv` was cut 800→143 MB).
- Presented two forms: **A** thin HTTP provider (scraper stays a separate service, `web_content`
  gets a `fetch_page` → `POST /api/1.0/scrap` provider + normalize), **B** port the browser stack
  into an in-process `web_scraper` module. Recommended A.

## Result

**Decision (user): skip.** The scraper is too heavy to bring in-process; keep it as a standalone
**daemon** (its own process/container). Do not extract it into `src/modules`. No code changed.

If browser-based fetch for hard sites is wanted later, revisit **form A** (thin HTTP `fetch_page`
provider to the daemon) — it adds nothing heavy to the platform.
