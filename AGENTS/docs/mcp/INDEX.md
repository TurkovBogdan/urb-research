# MCP server surface

Infrastructure for exposing a module **as an MCP server** under `/mcp/<code>` — each a separately mounted **standalone `fastmcp` fork** (3.4.1, +13 MB over the bundled `mcp`) Streamable-HTTP ASGI sub-app. `McpServer` = this surface (we *expose*), distinct from an MCP *client* (consume).

> **Current state:** bare core has no modules, so no MCP server is exposed and `app.state.mcp_servers` is empty. Only the mount mechanism + auth verifier (`src/core/mcp`) remain; the `app.state.mcp_servers` stash (set by `mount_mcp_servers`) stays for a future re-implementation. This describes the infra for when a new module declares an MCP server.

## Registration

Declarative `Module.mcp_servers: ClassVar[dict[str, McpServerBuilder]]` (mirror of `Module.guards`): key = `code` = URL segment, value = a **constructor fn always named `mcp_server`** (`(ctx) -> FastMCP`, **not** an instance → declaring the dict doesn't import fastmcp). Several servers per module are OK; a duplicate `code` across modules → `RuntimeError` at boot.

## Core foundation — `src/core/mcp/`

The **sole fastmcp import boundary**, backend-only — core infra, not a module (it edits the `Module` contract + mounts modules' apps):

- `context.py` — `McpServerContext{auth, audit, allowed_hosts}` + type aliases `TokenResolver` / `McpServerBuilder`, Protocol `McpPrincipal{id, group}`.
- `auth.py` — `McpServerTokenVerifier(TokenVerifier)`.
- `audit.py` — `McpServerAuditMiddleware` → channel `mcp/audit`.
- `factory.py` — `make_mcp_server(code, instructions, ctx)`.

Zone glue `core/router/mcp.py::mount_mcp_servers(app, modules, config) -> list[lifespan]`; `mounting.py` returns them; `app_factory.py` composes via `AsyncExitStack` inside lifespan (else the fork session manager never inits → 500).

## Auth

The mount bypasses FastAPI `dependencies=[...]`, so auth lives **inside** the server via the fork's `TokenVerifier.verify_token(token) -> AccessToken | None`. `McpServerTokenVerifier` is **agnostic** (no auth-module import): the resolver is INJECTED via `Module.mcp_token_resolver` (mirror of `guards`; `mount_mcp_servers` collects exactly one — supplied by a future auth module). The verifier calls `resolve(token, "mcp")` (scope-typed token check) → `AccessToken(client_id=str(id), scopes=[group])`. With no module providing a resolver, `mount_mcp_servers` short-circuits (no servers → returns `[]` before collecting one).

## Lazy-import discipline

Keeps the +13 MB out of the worker. `src/core/mcp` imports fastmcp at top, but is only imported **inside** the `mount_mcp_servers` body (not at `core/router/mcp.py` top — else the `app_factory`→`mounting` chain pulls it everywhere). A module's `mcp/__init__.py::mcp_server` must import `make_mcp_server` **in the fn body**, and tool files keep `from fastmcp import FastMCP` under `TYPE_CHECKING` (annotation only). Verified: `build_modules()` + worker boot (`server_enabled=False`) → `fastmcp` NOT in `sys.modules`. **Worker-clean invariant:** `build_modules()` must keep `fastmcp` out of `sys.modules` (the `mcp_servers` dict value is a fn, the builder import is lazy).

## Fork API gotchas (3.4.1, empirically verified)

The bundled-SDK assumptions don't hold.

- `FastMCP.http_app(path=..., transport="streamable-http", stateless_http=True, middleware=[...])` — the first positional is `path` NOT transport; pass transport as a kwarg.
- **MUST pass `path="/"` when mounting under `/mcp/<code>`** (2026-06-06 bug, fixed): the sub-app's default `streamable_http_path="/mcp"` (fastmcp settings), so under `app.mount("/mcp/<code>", sub)` the REAL endpoint silently lands at `/mcp/<code>/mcp` and `/mcp/<code>/` → 404 (307 from no-slash → 404). Client probe shows «Connection Failed / NO TOOLS». In-memory `Client(mcp)` + lifespan/mount-path tests DON'T catch it (they bypass HTTP routing). Regression: `test_app_factory::test_mcp_endpoint_served_at_code_root_not_double_mcp` (heavy, httpx ASGITransport: `/mcp/stub/`→401 not 404). A real `Bearer` mcp-token would be minted by a future auth module's token service (scope `"mcp"`).
- The fork constructor TAKES `version=` directly (no `_mcp_server.version` workaround).
- **No `TransportSecuritySettings` / `allowed_hosts` in the fork** (its `ssrf.py` = outbound SSRF, not Host rebinding). The code path exists at the ASGI layer: `http_app(middleware=[ASGIMiddleware(TrustedHostMiddleware, allowed_hosts=...)])`, fed by core `Config.mcp_allowed_hosts` (CSV → `mcp_allowed_hosts_list`). **Decision (remote MCP): leave `MCP_ALLOWED_HOSTS` empty** — our auth is **non-ambient Bearer** (the browser never auto-sends it), so DNS-rebinding yields a 401 → `allowed_hosts` is defense-in-depth, not essential. Host gate = nginx `server_name` + loopback bind (`SERVER_HOST=127.0.0.1`). nginx forwards `Host $host` (public domain), so IF set, the value = the public domain — but it's only needed if the backend port is exposed directly without nginx. Full threat-model in `AGENTS/research/fastmcp/fork-internals-security.md`.
- Server middleware = subclass `fastmcp.server.middleware.Middleware`, override `on_call_tool(ctx, call_next)`; tool name/args at `ctx.message.name`/`.arguments`; principal via `fastmcp.server.dependencies.get_access_token()` (returns None when unauthenticated — in-memory Client tests have no token).
- In-memory `Client(mcp)` bypasses auth (no transport); `call_tool().data` = reconstructed pydantic model (attr access); tool errors → `fastmcp.exceptions.ToolError` with the raised message passed through. **CAVEAT: in-memory `Client` is blind to auth AND HTTP routing** — it missed the mount-path bug above. For real coverage drive a fastmcp `Client` over `StreamableHttpTransport(url, auth=<token-str→Bearer>, httpx_client_factory=<factory→AsyncClient(transport=ASGITransport(app))>)` against an app mounted via the REAL `mount_mcp_servers`. Three gotchas: (a) the sub-app lifespan is an anyio task-group → enter/exit in ONE task → keep `async with` inside the test body, NOT a fixture (pytest-asyncio splits setup/teardown → "cancel scope in a different task"); (b) fastmcp calls the factory with extra kwargs (`follow_redirects`) → absorb `**_`; (c) the httpx client needs `follow_redirects=True` for `/mcp/<code>`→307→`/mcp/<code>/`. Invalid/missing token → Client connect raises.

Replaced the old APIRouter `build_mcp_zone` / `MCP_DEFAULT_GUARDS=["token"]` (never had a real guard). Plan/task `2026-06-06-mcp-server-surface`. Core tests: `tests/core/test_mcp_server_auth.py` (verifier), `tests/core/test_app_factory.py` (mount/dup-code/missing-resolver/lifespan, with a `stub` server). nginx side = `2026-06-05-nginx-mcp-streaming`.

## Adding a module MCP server

When a module declares one: `mcp/__init__.py::mcp_server(ctx)` calls `make_mcp_server` (lazy import) with instructions; tool files take `register(mcp: "FastMCP")` with `from fastmcp import FastMCP` under `TYPE_CHECKING`; `Module.mcp_servers = {"<code>": mcp_server}` (code is kebab, e.g. `"my-thing"`). The unified factory pins `version="0.1"`.

Give each server BOTH test layers (in-memory `Client(mcp)` + real-HTTP via `mount_mcp_servers`).

**Coverage gotcha:** `pytest --cov` UNDER-reports MCP tool bodies — fastmcp executes each tool in a worker thread the coverage tracer ignores by default, so tested `return`/branch lines show as missed. Run with `concurrency = thread,greenlet` (a `[run]` coveragerc via `--cov-config`) to get true numbers.

## HTTPS-only in prod

In prod the MCP server surface (`/mcp/<code>`, behind nginx + Cloudflare) is served **only over https/SSL**. Plain `http://` to the public origin returns Cloudflare `522` (origin doesn't answer on http) — **by design, not an outage** (user-stated; not derivable from code).

Consequences:

- When probing/debugging a prod MCP endpoint, use `https://` — an `http://` 522 is expected and does **not** mean the backend is down.
- A paste-ready client config must emit `https://` outside dev/test (an `app_env`-gated scheme rewrite) when a future module re-adds the connection-config surface.
- The client config `type` is `http` (streamable-HTTP transport); TLS comes from the `https://` URL, not from a `type:"https"`.
