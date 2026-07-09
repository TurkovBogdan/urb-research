---
name: feedback_no_backtick_wrapping
description: User dislikes inline-code backtick wrapping in chat replies
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0961e13c-00ff-4fc3-9ab2-b4b6ca439ad2
---

Don't wrap terms/identifiers in inline-code backticks in chat responses — the user asked for plain text (2026-07-04).

**Why:** the constant backtick formatting is visual noise the user doesn't want.
**How to apply:** write parameter names, statuses, method paths etc. as plain text in Russian chat replies. Code blocks (```json etc.) for actual code/JSON are still fine; this is about inline `x` wrapping of prose.
