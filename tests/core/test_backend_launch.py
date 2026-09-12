"""core/backend_launch: the launch line, the child environment, and the readiness probe.

The shared recipe of the MCP shim and the updater, tested directly — the callers only ever proved
their own control flow, which is how a restart that silently disabled the worker shipped green.
Nothing here starts a process: `Popen` is replaced, the probe answers from a stub.
"""

from __future__ import annotations

import subprocess
import sys
import types

import httpx
import pytest

from src.core import backend_launch
from src.core.backend_launch import (
    BackendHealth,
    backend_command,
    backend_environment,
    base_url,
    connect_host,
    health_url,
    preload_health_client,
    probe_health,
    spawn_backend,
    wait_until_ready,
)

LAUNCHER = ("uv", "run", "python")


def _cfg(**over):
    base = dict(server_host="127.0.0.1", server_port=12200)
    return types.SimpleNamespace(**{**base, **over})


def _health_response(payload, status_code=200):
    return types.SimpleNamespace(status_code=status_code, json=lambda: payload)


# ── the launch line ──────────────────────────────────────────────────────────

@pytest.mark.pure
def test_command_always_spells_out_the_http_role():
    command = backend_command(LAUNCHER)

    assert command[:3] == list(LAUNCHER)
    assert command[3].endswith("/src/app.py")
    assert command[4] == "--backend"


@pytest.mark.pure
@pytest.mark.parametrize(
    ("with_worker", "expected"),
    [(True, ["--worker"]), (False, ["--no-worker"]), (None, [])],
)
def test_command_states_the_worker_role_only_when_one_was_asked_for(with_worker, expected):
    command = backend_command(LAUNCHER, with_worker=with_worker)

    assert [token for token in command if "worker" in token] == expected


# ── the child environment ────────────────────────────────────────────────────

@pytest.mark.pure
def test_environment_forces_the_http_surface_on_and_reload_off():
    """`SERVER_ENABLED` defaults to False and no settings page writes it — unforced, the child
    would start nothing and exit 0."""
    environment = backend_environment()

    assert environment["SERVER_ENABLED"] == "true"
    assert environment["SERVER_HOT_RELOAD"] == "false"


@pytest.mark.pure
def test_environment_leaves_worker_enabled_alone_when_no_role_was_asked_for(monkeypatch):
    """The install's own `WORKER_ENABLED` must survive a restart: an env var outranks `.env`,
    so forcing a default here silently strips the scheduler off every update."""
    monkeypatch.setenv("WORKER_ENABLED", "true")

    assert backend_environment()["WORKER_ENABLED"] == "true"


@pytest.mark.pure
@pytest.mark.parametrize(("with_worker", "expected"), [(True, "true"), (False, "false")])
def test_environment_writes_the_requested_worker_role(with_worker, expected, monkeypatch):
    monkeypatch.setenv("WORKER_ENABLED", "true" if not with_worker else "false")

    assert backend_environment(with_worker=with_worker)["WORKER_ENABLED"] == expected


@pytest.mark.pure
def test_spawn_is_detached_with_its_output_in_a_file(monkeypatch, tmp_path):
    recorded = {}
    monkeypatch.setattr(
        backend_launch.subprocess, "Popen", lambda cmd, **kw: recorded.update(cmd=cmd, kw=kw)
    )

    command = spawn_backend(LAUNCHER, with_worker=True, log_path=tmp_path / "logs" / "backend.log")

    assert recorded["cmd"] == command
    assert recorded["kw"]["start_new_session"] is True
    assert recorded["kw"]["stdin"] is subprocess.DEVNULL
    assert (tmp_path / "logs" / "backend.log").exists()


# ── where the backend is reached ─────────────────────────────────────────────

@pytest.mark.pure
def test_connect_host_falls_back_to_loopback():
    assert connect_host(_cfg(server_host="0.0.0.0")) == "127.0.0.1"
    assert connect_host(_cfg(server_host="")) == "127.0.0.1"
    assert connect_host(_cfg(server_host="10.0.0.5")) == "10.0.0.5"


@pytest.mark.pure
def test_base_and_health_urls_use_the_connect_host():
    assert base_url(_cfg(server_port=9)) == "http://127.0.0.1:9"
    assert health_url(_cfg(server_port=9)) == "http://127.0.0.1:9/internal/health"


# ── readiness ────────────────────────────────────────────────────────────────

@pytest.mark.pure
def test_probe_reads_readiness_from_the_body_not_the_status_code(monkeypatch):
    monkeypatch.setattr(
        backend_launch.httpx,
        "get",
        lambda *a, **k: _health_response({"status": "degraded", "pending": ["rem_005", "wsm_004"]}),
    )

    health = probe_health(_cfg())

    assert health is not None
    assert health.is_ready is False
    assert health.pending == ("rem_005", "wsm_004")
    assert "rem_005, wsm_004" in health.describe()


@pytest.mark.pure
def test_probe_reports_ready_on_an_ok_payload(monkeypatch):
    monkeypatch.setattr(
        backend_launch.httpx, "get", lambda *a, **k: _health_response({"status": "ok"})
    )

    assert probe_health(_cfg()).is_ready is True


@pytest.mark.pure
def test_probe_is_none_when_the_backend_is_unreachable(monkeypatch):
    def _refuse(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(backend_launch.httpx, "get", _refuse)

    assert probe_health(_cfg()) is None


@pytest.mark.pure
def test_probe_is_none_on_an_unparsable_body(monkeypatch):
    def _not_json(*a, **k):
        return types.SimpleNamespace(
            status_code=200, json=lambda: (_ for _ in ()).throw(ValueError("not json"))
        )

    monkeypatch.setattr(backend_launch.httpx, "get", _not_json)

    assert probe_health(_cfg()) is None


@pytest.mark.pure
def test_wait_returns_the_health_once_the_backend_answers_ok(monkeypatch):
    states = iter([None, None, BackendHealth("ok")])
    monkeypatch.setattr(backend_launch, "probe_health", lambda config: next(states))
    monkeypatch.setattr(backend_launch.time, "sleep", lambda seconds: None)

    assert wait_until_ready(_cfg(), timeout=5).is_ready is True


@pytest.mark.pure
def test_wait_is_none_when_nothing_ever_answers(monkeypatch):
    monkeypatch.setattr(backend_launch, "probe_health", lambda config: None)
    monkeypatch.setattr(backend_launch.time, "sleep", lambda seconds: None)

    assert wait_until_ready(_cfg(), timeout=0) is None


@pytest.mark.pure
def test_wait_stops_on_a_degraded_backend_instead_of_sitting_out_the_timeout(monkeypatch):
    """A degraded backend is a refusal to serve, not a slow boot — the caller needs the reason,
    not a timeout."""
    probes = []
    degraded = BackendHealth("degraded", ("rem_005",))

    def _probe(config):
        probes.append(config)
        return degraded

    monkeypatch.setattr(backend_launch, "probe_health", _probe)
    monkeypatch.setattr(backend_launch.time, "sleep", lambda seconds: pytest.fail("kept waiting"))

    assert wait_until_ready(_cfg(), timeout=600) is degraded
    assert len(probes) == 1


@pytest.mark.pure
def test_the_health_probe_is_preloaded_in_one_call():
    """The updater must not import anything after `uv sync` has replaced the venv under it, and
    `httpx` builds its transport on first use — so the transport is built once, up front.
    Rehearsed 2026-09-13: without this the update imported 70+ modules after the sync."""
    preload_health_client()

    assert {"httpcore", "h11", "anyio", "certifi", "encodings.idna"} <= set(sys.modules)
