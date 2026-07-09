"""apps/app.mcp_stdio: шим — резолв кода, детект/спавн backend, браузер, прокси."""

from __future__ import annotations

import subprocess
import types

import httpx
import pytest

from src.apps.app import mcp_stdio


def _cfg(**over):
    base = dict(
        server_host="127.0.0.1", server_port=12200, app_log_level="INFO",
        mcp_token="", mcp_stdio_code="", mcp_stdio_start_worker=False,
        mcp_stdio_boot_timeout=30, mcp_stdio_open_browser=True,
    )
    return types.SimpleNamespace(**{**base, **over})


@pytest.mark.pure
def test_connect_host_falls_back_to_loopback():
    assert mcp_stdio._connect_host(_cfg(server_host="0.0.0.0")) == "127.0.0.1"
    assert mcp_stdio._connect_host(_cfg(server_host="")) == "127.0.0.1"
    assert mcp_stdio._connect_host(_cfg(server_host="10.0.0.5")) == "10.0.0.5"


@pytest.mark.pure
def test_base_url_uses_connect_host_and_port():
    assert mcp_stdio._base_url(_cfg(server_port=9)) == "http://127.0.0.1:9"


@pytest.mark.pure
def test_resolve_code_prefers_config():
    assert mcp_stdio._resolve_code(_cfg(mcp_stdio_code="explicit")) == "explicit"


@pytest.mark.pure
def test_resolve_code_picks_sole_mounted_server():
    """Пусто → единственный смонтированный модулями сервер (research)."""
    assert mcp_stdio._resolve_code(_cfg()) == "research"


@pytest.mark.pure
def test_backend_alive_true_on_200(monkeypatch):
    monkeypatch.setattr(
        mcp_stdio.httpx, "get", lambda *a, **k: types.SimpleNamespace(status_code=200)
    )
    assert mcp_stdio._backend_alive(_cfg()) is True


@pytest.mark.pure
def test_backend_alive_false_on_error(monkeypatch):
    def _boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(mcp_stdio.httpx, "get", _boom)
    assert mcp_stdio._backend_alive(_cfg()) is False


@pytest.mark.pure
def test_spawn_backend_command_env_and_detached(monkeypatch, tmp_path):
    rec = {}

    def _fake_popen(cmd, **kw):
        rec["cmd"] = cmd
        rec["kw"] = kw

    monkeypatch.setattr(mcp_stdio.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(mcp_stdio, "_backend_log_path", lambda c: tmp_path / "backend.log")

    mcp_stdio._spawn_backend(_cfg(mcp_stdio_start_worker=False))

    assert rec["cmd"][1].endswith("/app.py")
    assert "--backend" in rec["cmd"]
    assert "--worker" not in rec["cmd"]
    assert rec["kw"]["env"]["SERVER_ENABLED"] == "true"
    assert rec["kw"]["env"]["WORKER_ENABLED"] == "false"
    assert rec["kw"]["env"]["SERVER_HOT_RELOAD"] == "false"
    assert rec["kw"]["start_new_session"] is True
    assert rec["kw"]["stdin"] is subprocess.DEVNULL


@pytest.mark.pure
def test_spawn_backend_adds_worker_when_enabled(monkeypatch, tmp_path):
    rec = {}
    monkeypatch.setattr(mcp_stdio.subprocess, "Popen", lambda cmd, **kw: rec.update(cmd=cmd, kw=kw))
    monkeypatch.setattr(mcp_stdio, "_backend_log_path", lambda c: tmp_path / "backend.log")

    mcp_stdio._spawn_backend(_cfg(mcp_stdio_start_worker=True))

    assert "--worker" in rec["cmd"]
    assert rec["kw"]["env"]["WORKER_ENABLED"] == "true"


@pytest.mark.pure
def test_wait_ready_true_when_backend_comes_up(monkeypatch):
    states = iter([False, True])
    monkeypatch.setattr(mcp_stdio, "_backend_alive", lambda c: next(states))
    monkeypatch.setattr(mcp_stdio.time, "sleep", lambda s: None)
    assert mcp_stdio._wait_ready(_cfg(mcp_stdio_boot_timeout=5)) is True


@pytest.mark.pure
def test_wait_ready_false_on_timeout(monkeypatch):
    monkeypatch.setattr(mcp_stdio, "_backend_alive", lambda c: False)
    monkeypatch.setattr(mcp_stdio.time, "sleep", lambda s: None)
    assert mcp_stdio._wait_ready(_cfg(mcp_stdio_boot_timeout=0)) is False


@pytest.mark.pure
def test_ensure_backend_noop_when_alive(monkeypatch):
    calls = []
    monkeypatch.setattr(mcp_stdio, "_backend_alive", lambda c: True)
    monkeypatch.setattr(mcp_stdio, "_spawn_backend", lambda c: calls.append("spawn"))
    monkeypatch.setattr(mcp_stdio, "_open_home", lambda c: calls.append("browser"))
    mcp_stdio._ensure_backend(_cfg())
    assert calls == []


@pytest.mark.pure
def test_ensure_backend_boots_then_opens_browser(monkeypatch):
    calls = []
    monkeypatch.setattr(mcp_stdio, "_backend_alive", lambda c: False)
    monkeypatch.setattr(mcp_stdio, "_spawn_backend", lambda c: calls.append("spawn"))
    monkeypatch.setattr(mcp_stdio, "_wait_ready", lambda c: True)
    monkeypatch.setattr(mcp_stdio, "_open_home", lambda c: calls.append("browser"))
    mcp_stdio._ensure_backend(_cfg())
    assert calls == ["spawn", "browser"]


@pytest.mark.pure
def test_ensure_backend_raises_and_skips_browser_on_timeout(monkeypatch):
    calls = []
    monkeypatch.setattr(mcp_stdio, "_backend_alive", lambda c: False)
    monkeypatch.setattr(mcp_stdio, "_spawn_backend", lambda c: calls.append("spawn"))
    monkeypatch.setattr(mcp_stdio, "_wait_ready", lambda c: False)
    monkeypatch.setattr(mcp_stdio, "_open_home", lambda c: calls.append("browser"))
    with pytest.raises(RuntimeError):
        mcp_stdio._ensure_backend(_cfg())
    assert calls == ["spawn"]


@pytest.mark.pure
def test_open_home_respects_toggle(monkeypatch):
    opened = []
    monkeypatch.setattr(mcp_stdio.webbrowser, "open", lambda url: opened.append(url))
    mcp_stdio._open_home(_cfg(mcp_stdio_open_browser=False))
    assert opened == []
    mcp_stdio._open_home(_cfg(server_port=8080, mcp_stdio_open_browser=True))
    assert opened == ["http://127.0.0.1:8080/"]


@pytest.mark.pure
def test_build_proxy_targets_backend_mcp_url():
    proxy = mcp_stdio._build_proxy(_cfg(server_port=8080), "research")
    assert proxy.name == "research"


@pytest.mark.pure
def test_file_only_logging_omits_stdout_handler():
    """Фабрика шима даёт логгер без stdout-хендлера (только файл) — stdout под MCP."""
    import logging
    import sys

    from src.core.loggers.logger_store import LoggerStore

    try:
        mcp_stdio._use_file_only_logging(_cfg())
        handlers = LoggerStore.get("mcp")._logger.handlers
        assert any(isinstance(h, logging.FileHandler) for h in handlers)
        assert not any(
            type(h) is logging.StreamHandler and getattr(h, "stream", None) is sys.stdout
            for h in handlers
        )
    finally:
        LoggerStore.reset()


@pytest.mark.pure
def test_run_mcp_stdio_boots_backend_then_runs_proxy(monkeypatch):
    calls = []
    monkeypatch.setattr(mcp_stdio, "_use_file_only_logging", lambda c: None)
    monkeypatch.setattr(mcp_stdio, "_resolve_code", lambda c: "research")
    monkeypatch.setattr(mcp_stdio, "_ensure_backend", lambda c: calls.append("ensure"))

    class _FakeProxy:
        def run(self, show_banner):
            calls.append(("run", show_banner))

    monkeypatch.setattr(mcp_stdio, "_build_proxy", lambda c, code: _FakeProxy())
    mcp_stdio.run_mcp_stdio(_cfg())
    assert calls == ["ensure", ("run", False)]
