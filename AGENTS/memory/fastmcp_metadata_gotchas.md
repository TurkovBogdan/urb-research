---
name: FastMCP metadata gotchas
description: FastMCP server metadata wire behavior — version isn't forwarded by constructor, title is never sent over MCP wire; how McpClient reads a peer server's metadata
type: reference
originSessionId: cd37e76d-088a-48fe-ba69-3725c007e0cd
---
FastMCP exposes incomplete metadata through its constructor. We no longer run our own
FastMCP servers (the `src/apps/mcp_*` servers were removed), but `llm_providers` is still
an MCP **client** ([[project_llm_providers_mcp_servers]]) — these wire facts govern what it
can read from a peer server via `McpClient`:

- **`name`** — `FastMCP("name", ...)` 1st arg; reaches clients as the tool namespace.
- **`instructions`** — `FastMCP(..., instructions="...")`; reaches clients via `InitializeResult.instructions`.
- **`version`** — NOT in `FastMCP.__init__`; set after construction `mcp._mcp_server.version = "0.5"`; reaches clients via `serverInfo.version`.
- **`title`** — NOT in the low-level `Server` at all; cannot be sent over the wire with the current SDK. A peer reporting `serverInfo.title` will be `None` unless a future SDK adds it server-side.
- **`website_url`, `icons`** — constructor kwargs.

**Why:** SDK design limitation as of the `mcp` package version in `uv.lock`. Low-level
`Server.__init__` accepts only `name/version/instructions/website_url/icons/lifespan`.

**Reading a peer server's metadata** (via `McpClient`, used by `/mcp/servers/{code}/probe`):
`server_info` returns `(name, version)`, `server_title` reads `serverInfo.title` (usually
`None`, see above), `instructions` reads `init_result.instructions`.
