"""Degraded serve — the schema is behind the code, so nothing but health answers.

`mark_degraded(app, pending)` records the verdict in `app.state`; `PendingMigrationsGate`
answers every request 503 (JSON under the machine zones, an HTML stub elsewhere) while it is
set, with `/internal/health` exempt and reporting `degraded` at 200. Why a stub rather than a
raising lifespan: `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from fastapi import FastAPI
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.router.api import API_PREFIX
from src.core.router.mcp import MCP_PREFIX
from src.core.router.storage import STORAGE_PREFIX

DEGRADED_STATUS_CODE = 503
HEALTH_STATUS_OK = "ok"
HEALTH_STATUS_DEGRADED = "degraded"
PENDING_MIGRATIONS_CODE = "migrations_pending"

# Zones whose clients parse a body; everything else is a browser and gets the stub page.
MACHINE_ZONE_PREFIXES = (API_PREFIX, MCP_PREFIX, STORAGE_PREFIX)

_UPDATE_INSTRUCTION = (
    "Re-run the update script (./update.sh) on the host to bring the database to head."
)


def mark_degraded(app: FastAPI, pending: Sequence[str]) -> None:
    """Record that this app must not serve data: its schema is behind `pending` revisions."""
    app.state.degraded = {"pending": list(pending)}


def degraded_pending(app: FastAPI) -> list[str] | None:
    """The pending revisions while the app serves degraded, else None."""
    degraded = app.state.degraded
    return None if degraded is None else list(degraded["pending"])


def health_payload(app: FastAPI) -> dict[str, object]:
    """Body of `/internal/health`. Degraded still answers 200 — a non-200 makes the MCP shim
    declare the backend dead and spawn a second one."""
    pending = degraded_pending(app)
    if pending is None:
        return {"status": HEALTH_STATUS_OK}
    return {"status": HEALTH_STATUS_DEGRADED, "pending": pending}


class PendingMigrationsGate:
    """Short-circuits every request while the app is marked degraded; one path stays exempt."""

    def __init__(self, app: ASGIApp, *, exempt_path: str) -> None:
        self._app = app
        self._exempt_path = exempt_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        gated = scope["type"] == "http" and scope["path"] != self._exempt_path
        pending = degraded_pending(scope["app"]) if gated else None
        if pending is None:
            await self._app(scope, receive, send)
            return
        await _refusal(scope["path"], pending)(scope, receive, send)


def mount_degraded_gate(app: FastAPI, *, health_path: str) -> None:
    """Register the gate LAST: `add_middleware` inserts at position 0, so the last one added is
    the outermost — the gate must sit outside `mount_spa`'s middleware, which would otherwise
    answer browser GETs with the SPA before the gate ever ran."""
    app.add_middleware(PendingMigrationsGate, exempt_path=health_path)


def _refusal(path: str, pending: Sequence[str]) -> Response:
    if _under_zone_prefix(path, MACHINE_ZONE_PREFIXES):
        return JSONResponse(_error_body(pending), status_code=DEGRADED_STATUS_CODE)
    return HTMLResponse(_stub_page(pending), status_code=DEGRADED_STATUS_CODE)


def _under_zone_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)


def _reason(pending: Sequence[str]) -> str:
    return (
        f"The database schema is behind the code: {len(pending)} migration(s) not applied "
        f"({', '.join(pending)}). {_UPDATE_INSTRUCTION}"
    )


def _error_body(pending: Sequence[str]) -> dict[str, object]:
    return {
        "error": _reason(pending),
        "code": PENDING_MIGRATIONS_CODE,
        "pending": list(pending),
    }


def _stub_page(pending: Sequence[str]) -> str:
    revisions = "\n".join(f"      <li><code>{escape(revision)}</code></li>" for revision in pending)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Update required</title>
    <style>
      body {{ font: 16px/1.6 system-ui, sans-serif; margin: 0; padding: 48px 24px;
             color: #1f2430; background: #f6f7f9; }}
      main {{ max-width: 640px; margin: 0 auto; background: #fff; border-radius: 12px;
              padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,.12); }}
      h1 {{ font-size: 22px; margin: 0 0 16px; }}
      code {{ font-family: ui-monospace, monospace; background: #eef0f4; border-radius: 4px;
              padding: 1px 5px; }}
      ul {{ padding-left: 20px; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Update required — the app is not serving data</h1>
      <p>
        The code in this checkout is newer than the database schema, so the application refuses
        to read or write anything until the migrations are applied.
      </p>
      <p>Not applied ({len(pending)}):</p>
      <ul>
{revisions}
      </ul>
      <p>{escape(_UPDATE_INSTRUCTION)}</p>
    </main>
  </body>
</html>
"""


__all__ = [
    "DEGRADED_STATUS_CODE",
    "HEALTH_STATUS_DEGRADED",
    "HEALTH_STATUS_OK",
    "MACHINE_ZONE_PREFIXES",
    "PENDING_MIGRATIONS_CODE",
    "PendingMigrationsGate",
    "degraded_pending",
    "health_payload",
    "mark_degraded",
    "mount_degraded_gate",
]
