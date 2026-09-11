"""Starting a detached backend and waiting for it to answer — one recipe, two callers:
the MCP shim and the updater.

`spawn_backend(launcher, with_worker, log_path)` starts `src/app.py --backend` in a new session
with its output in a log file; `wait_until_ready` / `probe_health` read `/internal/health` and
report readiness from the body (`status == "ok"`), never from the status code alone. The
launcher is a parameter because the updater cannot reuse `sys.executable` after `uv sync`.
Rationale for the flags and the environment: `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx

from src.core.app_path import project_root

APP_ENTRY = project_root() / "src" / "app.py"

# How the updater reaches a Python that exists after `uv sync`.
UV_RUN_PYTHON = ("uv", "run", "python")

HEALTH_PATH = "/internal/health"
HEALTH_STATUS_OK = "ok"

PROBE_TIMEOUT_SECONDS = 1.0
READY_POLL_SECONDS = 0.3


def backend_command(launcher: Sequence[str], *, with_worker: bool | None = None) -> list[str]:
    """The launch line; `with_worker=None` leaves the background role to the child's own config."""
    command = [*launcher, str(APP_ENTRY), "--backend"]
    if with_worker is not None:
        command.append("--worker" if with_worker else "--no-worker")
    return command


def backend_environment(*, with_worker: bool | None = None) -> dict[str, str]:
    """Role in the environment as well as in argv: uvicorn's reload child inherits env, not flags.

    `WORKER_ENABLED` is only written when a role was asked for — an environment variable outranks
    the install's `.env`, so forcing a default here would turn every restart into a silent change
    of what the install runs.
    """
    environment = dict(os.environ)
    environment["SERVER_ENABLED"] = "true"
    environment["SERVER_HOT_RELOAD"] = "false"
    if with_worker is not None:
        environment["WORKER_ENABLED"] = "true" if with_worker else "false"
    return environment


def spawn_backend(
    launcher: Sequence[str], *, with_worker: bool | None = None, log_path: Path
) -> list[str]:
    """Start the backend detached; returns the command so the caller can report it."""
    command = backend_command(launcher, with_worker=with_worker)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    backend_log = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — наследует потомок
    subprocess.Popen(
        command,
        cwd=str(project_root()),
        env=backend_environment(with_worker=with_worker),
        stdin=subprocess.DEVNULL,
        stdout=backend_log,
        stderr=backend_log,
        start_new_session=True,
    )
    return command


@dataclass(frozen=True)
class BackendHealth:
    """The parsed `/internal/health` body.

    A 200 on its own says nothing about readiness: a backend whose migration chain is behind
    answers 200 with `status="degraded"` (a non-200 would read as death, and a caller would go
    spawn a second server).
    """

    status: str
    pending: tuple[str, ...] = ()

    @property
    def is_ready(self) -> bool:
        return self.status == HEALTH_STATUS_OK

    def describe(self) -> str:
        if not self.pending:
            return f"статус «{self.status}»"
        return f"статус «{self.status}», не применены ревизии: {', '.join(self.pending)}"


def connect_host(config) -> str:
    """Host for a local connection to the backend: 0.0.0.0/empty → 127.0.0.1."""
    return config.server_host if config.server_host not in ("", "0.0.0.0") else "127.0.0.1"


def base_url(config) -> str:
    return f"http://{connect_host(config)}:{config.server_port}"


def health_url(config) -> str:
    return base_url(config) + HEALTH_PATH


def probe_health(config) -> BackendHealth | None:
    """The backend's state; None when it is unreachable, answered non-200 or not a JSON object."""
    try:
        response = httpx.get(health_url(config), timeout=PROBE_TIMEOUT_SECONDS)
        payload = response.json() if response.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return BackendHealth(
        status=str(payload.get("status", "")),
        pending=tuple(str(revision) for revision in payload.get("pending") or ()),
    )


def wait_until_ready(config, *, timeout: float) -> BackendHealth | None:
    """Poll health until the backend is ready or the deadline passes.

    Returns the last state seen, so a caller can name the reason; None when nothing ever
    answered. A degraded backend ends the wait immediately — it is a refusal to serve data, not
    a slow boot, and waiting out the timeout would hide the pending revisions behind «too slow».
    """
    deadline = time.monotonic() + timeout
    last_seen: BackendHealth | None = None
    while True:
        health = probe_health(config)
        if health is not None:
            last_seen = health
            if health.is_ready or health.pending:
                return health
        if time.monotonic() >= deadline:
            return last_seen
        time.sleep(READY_POLL_SECONDS)


__all__ = [
    "APP_ENTRY",
    "HEALTH_PATH",
    "HEALTH_STATUS_OK",
    "UV_RUN_PYTHON",
    "BackendHealth",
    "backend_command",
    "backend_environment",
    "base_url",
    "connect_host",
    "health_url",
    "probe_health",
    "spawn_backend",
    "wait_until_ready",
]
