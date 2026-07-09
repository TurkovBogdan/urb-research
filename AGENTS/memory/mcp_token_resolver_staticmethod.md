---
name: mcp_token_resolver_staticmethod
description: A function assigned to a Module ClassVar hook (mcp_token_resolver) binds as a method — use staticmethod
metadata: 
  node_type: memory
  type: project
  originSessionId: 39d62107-5343-4d74-a7ca-77b10d34a835
---

Assigning a bare **function** to a class-attribute hook (`Module.mcp_token_resolver = resolve_mcp_token`)
makes it a **bound method** on instance access: `_collect_resolver` reads `m.mcp_token_resolver` →
`resolve_mcp_token.__get__(m)`, so calling `(token, scope)` passes `(m, token, scope)` → `TypeError: takes 2
positional arguments but 3 were given`. Latent — only fires once an MCP client actually authenticates (empty
`MCP_TOKEN` / no client never calls the resolver), so it surfaced as a **500** only when token auth was turned on.

**Fix:** wrap in `staticmethod` at the assignment site — `mcp_token_resolver = staticmethod(resolve_mcp_token)`
(honors the base `ClassVar["TokenResolver | None"]` = a plain callable). Applies to any function-valued
`ClassVar` hook on a Module; dict/instance hooks (`mcp_servers`) don't bind. See [[fastmcp_metadata_gotchas]].
