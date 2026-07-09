---
title: Group docs/ root files into area subdirs
date: 2026-06-07
status: completed
description: "Move the 24 flat AGENTS/docs root docs into area subdirs (platform/, frontend/, workflow/, twenty/) and drop now-redundant core-/frontend- prefixes; fix all inbound links."
tags: [agents, docs]
---

## Task

User: docs/ root still has many flat docs after the restructure — group everything into subdirs (chose option B). Drop now-redundant `core-`/`frontend-` prefixes.

## Context

Follows `2026-06-07-agent-memory-restructure`. Navigation axis = modules (subdir per module). Root had 24 flat cross-cutting docs grouped only by filename prefix; `platform/` (2) + `mcp/` (1) were thin new subdirs inconsistent with the flat platform docs. Decision: commit to area subdirs for ALL non-module docs.

## Move map (docs-root-relative)

- platform/: core-architecture→architecture, core-module-system→module-system, core-locks→locks, core-loggers→loggers, api-zones, router, permissions, database, migrations, soft-delete, dates (+ existing overview, run-configs)
- frontend/: frontend-route-meta→route-meta, frontend-validators→validators, frontend-layout→layout, frontend-api-client→api-client, frontend-rules→rules, vuetify-css-patterns, design-system, i18n, markdown-rendering
- workflow/: testing, benches, debugging
- twenty.md → twenty/INDEX.md
- unchanged: INDEX.md (root), mcp/, conventions/, and all module subdirs

## What was done

- `git mv` of 24 docs into `platform/` (11, prefix dropped: architecture/module-system/locks/loggers + api-zones/router/permissions/database/migrations/soft-delete/dates), `frontend/` (9, prefix dropped: route-meta/validators/layout/api-client/rules + vuetify-css-patterns/design-system/i18n/markdown-rendering), `workflow/` (3: testing/benches/debugging), `twenty/INDEX.md`. docs/ root now = `INDEX.md` + subdirs only.
- Fixed 213 inbound links via 3 sub-agents on disjoint file sets (docs/INDEX.md; all other docs/; memory-gotchas + education) + central edits (MEMORY.md routing table, agent-primary.md). Each link verified with `test -f`.
- Caught + fixed depth breakage on moved files' OUTBOUND links escaping docs/ (needed extra `../`: dev/docs, tests, src) + 2 pre-existing dangling links to memory files deleted in the prior refactor (`migration_cross_module_depends_on`→`conventions/db-migrations`, `versioning_pattern`→`conventions/backend`) that the earlier validation had missed.
- Fixed a self-introduced bad playbook link in agent-primary.md (repo-root-relative path).

## Result

- docs/ fully on the subdir axis: `conventions/ conversation_insights/ conversations/ core_geo/ core_monitoring/ core_security/ core_users/ frontend/ intercom/ llm_providers/ mail_sync/ mcp/ platform/ twenty/ workflow/` + root `INDEX.md`.
- **Link validation green:** all file-relative links under docs/memory/education resolve; agent-primary.md repo-root-relative links resolve.
- Not committed (commit protocol).
