---
title: Plan title
date: YYYY-MM-DD
status: in-work  # in-work | completed | deferred
description: "Short summary of what is being planned. One or two sentences."
tags: [area, subsystem]
---

## Goal

What outcome this plan achieves. Stated as a finished state, not an activity ("auth uses signed cookies", not "refactor auth").

## Context

Current state and why it needs to change: constraints, prior decisions, related work. Link to relevant files, memory entries, research notes.

## Scope

**In scope:**
- ...

**Out of scope:**
- ...

## Approach

High-level strategy in a few sentences. Why this approach was chosen over alternatives — name at least one alternative considered and the reason it was rejected.

## Steps

Ordered, concrete, independently verifiable. Each step should be small enough to land as a single commit / review unit.

1. Step — files touched: `path/to/file`
2. Step — files touched: `path/to/file`
3. Step — files touched: `path/to/file`

## Tests

Tests to add or update as part of this plan. Cover the new behavior, regressions, and edge cases — not just the happy path.

- Unit: ... — covers ...
- Integration: ... — covers ...
- E2E / manual: ... — covers ...

## Validation

How we know it worked beyond tests: manual checks, metrics, logs, or behavior to observe in a running environment.

- ...

## Risks / open questions

- Risk: ... — mitigation: ...
- Open question: ... — needs answer before step N.

## References

- Related tasks: `AGENTS/tasks/YYYY-MM-DD-slug.md`
- Memory entries: `AGENTS/memory/topic.md`
- Research: `AGENTS/research/topic/INDEX.md`
- External docs / tickets: <url>
