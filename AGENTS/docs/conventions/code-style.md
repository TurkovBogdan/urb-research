# Code style — self-documenting code

Read before writing or refactoring any code (backend Python or frontend TS/Vue). This is the
**top-priority readability rule the user enforces**: the code must explain itself through its
**structure and names**, not through comments. Comments are a fallback for *why*, never a crutch for
*what*.

## The rule

**Make the code self-documenting. Names carry the meaning; comments only justify the non-obvious.**

When a piece of logic is unclear, the fix is to **extract and name it**, NOT to add a comment in front
of it. If you reach for a comment that restates what the next line does, that comment is a smell —
replace it with a named variable, predicate, or function whose name says the same thing.

Concretely:

- **Name every non-trivial sub-expression.** A boolean condition, a query, an intermediate value — bind
  it to a variable whose name states intent (`never_tagged`, `content_changed`, `outdated_in_tier`),
  instead of leaving an inline expression with a comment above it.
- **No label/enumeration comments standing in for names.** `# Tier 1 — …`, `# Step 2 …`, `# case A`
  above a block means the block should be a named thing (`tiers_by_priority`, a named function/predicate)
  whose name and ordering convey the same structure.
- **Descriptive identifiers, not abbreviations.** `conversation_id` not `cid`; `outdated_in_tier` not
  `stmt`; `conversation_with_live_result` not `base`. The call site should read like a sentence.
- **Comments explain WHY, not WHAT.** Keep a comment only when it records a reason the code cannot show
  on its own — a gotcha, an invariant, a non-obvious ordering constraint, a link to an external quirk.
  Never narrate the mechanics the names already make obvious.
- **No reference/prose comments in code.** Design rationale, tier tables, and multi-sentence
  explanations belong in `AGENTS/docs/` (or a docstring's one-liner), not interleaved with statements.
  A docstring states the contract briefly; the body shows the rest by construction.
- **Let structure encode the invariant.** Order, grouping, and composition should make a property
  visible. Mutually-exclusive cases should *look* mutually exclusive in the source.

**Why:** comments rot — they drift out of sync with code and silently lie. Names are checked by the
reader on every change and by tooling on rename. Code that reads top-to-bottom as intent needs no
narration; the next person (or agent) understands it from the identifiers alone. This is also why the
docs tier exists: prose has a home (`docs/`), so the code can stay prose-free.

**How to apply:** before adding any comment, ask "can a name say this?" — if yes, extract a named
variable/predicate/function instead. Reserve comments for the *why* of something genuinely surprising.
Audit your own diff: every `# <what the next line does>` comment is a refactor request, not a
deliverable.

## Worked example — priority-tier selection

A priority-tier selection (`pick_outdated_*_ids`) was first written with numbered comments
in front of each query (`# Tier 1 - never tagged`, `# Tier 2 - content changed`, …) and terse names
(`base`, `stmt`, `cid`, a `_take` closure). That is the anti-pattern: the comments carried the meaning
the code did not.

Self-documenting rewrite — the names and the tuple's shape say everything the comments used to:

```python
never_tagged = r.id.is_(None)
content_changed = r.content_hash.is_distinct_from(c.content_hash)
version_drifted = (
    r.agent_version.is_distinct_from(agent_version)
    | r.tagger_version.is_distinct_from(tagger_version)
)

# order = priority; the `~never_tagged & ~content_changed` chain makes the tiers mutually exclusive
tiers_by_priority = (
    never_tagged,
    ~never_tagged & content_changed,
    ~never_tagged & ~content_changed & version_drifted,
)
```

- `never_tagged` / `content_changed` / `version_drifted` — the *reason* a conversation is outdated reads
  off the name; no comment needed.
- `tiers_by_priority` — the variable name states that order means priority; the `~…` composition makes
  the disjointness visible in the source instead of explaining it in prose.
- `conversation_with_live_result`, `outdated_in_tier`, `conversation_id` — every identifier in the loop
  is a phrase, so the body reads as a sentence.

The one surviving comment explains a *why* the code cannot show (that the negation chain is what keeps
tiers disjoint) — that is the only legitimate use.
