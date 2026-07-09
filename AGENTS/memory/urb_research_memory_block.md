---
name: urb_research_memory_block
description: "urb-research MCP is a general knowledge/memory block, not only research — central store of artifacts (research reports, migration designs, agent instructions) reusable across projects."
metadata: 
  node_type: memory
  type: project
  originSessionId: 30865207-6b13-4302-b157-d2c2e2e96ddf
---

The `urb-research` MCP being designed in `AGENTS/obsidian/` (symlink to second-brain) is conceptually a **central memory block**, not just a research tool: one local store of **knowledge artifacts** for all the user's projects — research reports, migration designs, agent instructions, decisions — with cross-project reuse and semantic (vector) search.

Research is the **first surface** being designed, but the storage + search model is meant to be general for any artifact type. Storage layer (designed bottom-up): a relational DB for raw documents/artifacts + a **separate vector DB** for embeddings — two stores means no FK between them, so the chunk↔vector link is application-level by key (`chunk_id`/`content_hash`).

Design home (single source): `AGENTS/obsidian/00-overview.md`, `general.canvas` (top-down view + bottom-up layered architecture), `pipeline.canvas`, `tables.canvas`. Status: design only, no code yet.

**Why:** the framing changes the data model — `document` is one origin (external scrape); produced artifacts are another origin feeding the same chunk→vector pipeline.

**How to apply:** when designing/implementing, don't hard-bind the schema or tools to "research"; keep the artifact model generic. Reflect design decisions on the canvases, not only in chat.
