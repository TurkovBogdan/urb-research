# MCP stdio shim — wake-on-demand backend

Role `--mcp-stdio` (`src/apps/app/mcp_stdio.py`) — a lazy launcher so **nothing runs
idle**. The MCP client spawns this process over **stdio** (`command:` transport, not
`url:`); on start it boots the HTTP backend on demand, opens the browser, and bridges
tool calls to the backend's `/mcp/<code>`.

## Why

MCP servers are mounted **inside** the HTTP backend (`app.mount("/mcp/<code>")`,
`core/router/mcp.py`), so an HTTP-transport MCP request can only be received by an
already-running server — you can't "wake" an HTTP listener that isn't there. Switching
the local client to a **stdio** server flips the trigger: the client itself spawns our
process when its MCP session opens, so at rest there is no backend, no proxy, nothing.

## Flow (`run_mcp_stdio`)

1. `_resolve_code` — the proxied MCP server code: `MCP_STDIO_CODE`, else the sole
   server mounted by `build_modules()` (here `research`).
2. `_ensure_backend`:
   - `_backend_alive` probes `GET /internal/health` on `127.0.0.1:SERVER_PORT`.
   - If down → `_spawn_backend` runs `src/app.py --backend` (`+ --worker` iff
     `MCP_STDIO_START_WORKER`) as a **detached** process (`start_new_session=True`) with
     its stdio sent to `logs/mcp_stdio_backend.log` — **never** the client's stdio pipe.
     `SERVER_ENABLED=true`, `SERVER_HOT_RELOAD=false` are forced in its env.
   - `_wait_ready` polls health up to `MCP_STDIO_BOOT_TIMEOUT`s (else `RuntimeError`).
   - `_open_home` opens the system browser at `http://127.0.0.1:SERVER_PORT/` — **only
     when we actually booted** the backend (a reused, already-live backend keeps its tab;
     don't spam a new one). Gated by `MCP_STDIO_OPEN_BROWSER`.
3. `_build_proxy` — `create_proxy(StreamableHttpTransport(<backend>/mcp/<code>,
   auth=MCP_TOKEN or None))` (fastmcp `fastmcp.server.create_proxy`); `proxy.run(
   show_banner=False)` serves stdio and forwards every call to the backend.

**Lifecycle:** the backend **outlives the shim** — closing the MCP session kills the
shim, the backend keeps running (reused by the next session). Stop it **manually** (no
idle shutdown, by design). Auth: the shim sends `MCP_TOKEN` as Bearer, matching the
backend's draft resolver (`research/mcp/auth.py`); empty token = allow-all (local).

## Invariants

- **stdout is sacred** — it carries the MCP protocol; a stray line breaks JSONRPC.
  `CoreLogger` defaults `stdout=True`, so `run_mcp_stdio` first calls
  `_use_file_only_logging` (a `set_logger_factory` with `stdout=False`) — logs go to
  `logs/mcp.log` only. The backend subprocess's stdio is detached to its own log file.
- **Lazy fastmcp** — importing `mcp_stdio` must not pull `fastmcp` (+13 MB); the import
  lives inside `_build_proxy`. Same worker-clean rule as the rest of the MCP infra
  ([mcp/INDEX](../mcp/INDEX.md)).

## Config (`Config`, env `MCP_STDIO_*`)

| key | default | meaning |
|-----|---------|---------|
| `MCP_STDIO_OPEN_BROWSER` | `true` | open the system browser on the home page after boot |
| `MCP_STDIO_START_WORKER` | `false` | also boot the scheduler/worker (research/search are synchronous → off) |
| `MCP_STDIO_BOOT_TIMEOUT` | `30` | seconds to wait for `/internal/health` after spawn |
| `MCP_STDIO_CODE` | `""` | proxied server code; empty → the sole mounted one |

## Client config (switch transport to `command`)

```json
{
  "mcpServers": {
    "urb-research": {
      "command": "/path/to/uv",
      "args": [
        "run", "--directory", "/path/to/urb-research",
        "python", "src/app.py", "--mcp-stdio"
      ]
    }
  }
}
```

**Use `uv run --directory <project>` with an absolute `uv` path — do NOT rely on the
client's `cwd`.** Many MCP clients spawn the command from their own working dir and with
a minimal PATH; without `--directory`, `uv run` runs outside the project (can't find
`src/app.py`, grabs the wrong interpreter instead of the project venv → "Connection
Failed / NO TOOLS"). `--directory` makes the command self-contained (no `cwd` needed).

Replaces the previous `url: http://…:SERVER_PORT/mcp/research` (streamable-HTTP) entry.
Local-only model; a remote prod deploy keeps the HTTP backend running behind nginx.

## Tests

`tests/apps/test_mcp_stdio.py` (pure, mocked subprocess/httpx/webbrowser) +
`tests/apps/test_app.py` (flag parse + `main` dispatch). Live bridge verified against a
running backend: `create_proxy` lists all 23 `research` tools through the token.
