"""app: CLI-флаги, проброс в env (флаг > env), диспетчеризация роли + migrate."""

from __future__ import annotations

import sys
import types

import pytest

import app


def _fake_config(**over):
    """Лёгкий стенд под Config для _run_server/_run_worker (без БД)."""
    base = dict(
        server_host="127.0.0.1", server_port=12200, app_log_level="INFO",
        server_hot_reload=False, server_processes=1,
        worker_modules_set=None, worker_max_concurrent_runs=10,
        worker_tick_seconds=5,
    )
    return types.SimpleNamespace(**{**base, **over})


@pytest.fixture
def _pin_role_env(monkeypatch):
    """Зафиксировать role-env валидными значениями, чтобы прямые записи main()
    откатились на teardown (monkeypatch вернёт исходное)."""
    for key, val in (
        ("SERVER_ENABLED", "false"), ("WORKER_ENABLED", "false"),
        ("SERVER_HOT_RELOAD", "false"), ("WORKER_MODULES", ""),
        ("WORKER_TICK_SECONDS", "5"), ("WORKER_MAX_CONCURRENT_RUNS", "10"),
    ):
        monkeypatch.setenv(key, val)


@pytest.mark.pure
def test_parse_defaults_are_none():
    """Без флагов — все тогглы None (роль берётся из env)."""
    a = app._parse_args([])
    assert a.backend is None
    assert a.worker is None
    assert a.hot_reload is None
    assert a.worker_module is None
    assert a.processes is None


@pytest.mark.pure
def test_parse_backend_worker_flags():
    a = app._parse_args(["--backend", "--worker"])
    assert a.backend is True
    assert a.worker is True


@pytest.mark.pure
def test_parse_negated_flags():
    a = app._parse_args(["--no-backend", "--no-hot-reload"])
    assert a.backend is False
    assert a.hot_reload is False


@pytest.mark.pure
def test_parse_mcp_stdio_flag():
    assert app._parse_args([]).mcp_stdio is False
    assert app._parse_args(["--mcp-stdio"]).mcp_stdio is True


@pytest.mark.pure
def test_worker_module_is_repeatable():
    a = app._parse_args(["--worker-module", "alpha", "--worker-module", "beta"])
    assert a.worker_module == ["alpha", "beta"]


@pytest.mark.pure
def test_apply_env_overrides_sets_env(monkeypatch):
    for key in (
        "SERVER_ENABLED", "WORKER_ENABLED", "SERVER_HOT_RELOAD",
        "WORKER_MODULES", "WORKER_TICK_SECONDS", "WORKER_MAX_CONCURRENT_RUNS",
    ):
        monkeypatch.delenv(key, raising=False)
    args = app._parse_args(
        ["--backend", "--no-worker", "--worker-module", "a", "--worker-module", "b",
         "--worker-tick-seconds", "9", "--worker-max-concurrent", "3"]
    )
    app._apply_env_overrides(args)
    import os

    assert os.environ["SERVER_ENABLED"] == "true"
    assert os.environ["WORKER_ENABLED"] == "false"
    assert os.environ["WORKER_MODULES"] == "a,b"
    assert os.environ["WORKER_TICK_SECONDS"] == "9"
    assert os.environ["WORKER_MAX_CONCURRENT_RUNS"] == "3"


@pytest.mark.pure
def test_apply_env_overrides_skips_unset(monkeypatch):
    """None-флаги env не трогают (остаётся прежнее значение)."""
    monkeypatch.setenv("SERVER_ENABLED", "false")
    app._apply_env_overrides(app._parse_args([]))
    import os

    assert os.environ["SERVER_ENABLED"] == "false"


@pytest.mark.pure
def test_host_port_processes_not_pushed_to_env(monkeypatch):
    """--host/--port/--processes идут в _run_server напрямую, НЕ в env."""
    for key in ("SERVER_HOST", "SERVER_PORT", "SERVER_PROCESSES"):
        monkeypatch.delenv(key, raising=False)
    app._apply_env_overrides(
        app._parse_args(["--host", "0.0.0.0", "--port", "9", "--processes", "4"])
    )
    import os

    assert "SERVER_HOST" not in os.environ
    assert "SERVER_PORT" not in os.environ
    assert "SERVER_PROCESSES" not in os.environ


# ── env → Config (флаг > env > дефолт) ──────────────────────────────────────


@pytest.mark.pure
def test_env_drives_role_in_config(monkeypatch):
    """env-тогглы доходят до Config (env > дефолт)."""
    monkeypatch.setenv("SERVER_ENABLED", "false")
    monkeypatch.setenv("WORKER_ENABLED", "true")
    from src.core.config import Config

    c = Config(_env_file=None, db_host="x", db_name="x", db_user="x",
               db_password="x", db_ssl=False)
    assert c.server_enabled is False
    assert c.worker_enabled is True


@pytest.mark.pure
def test_flag_overrides_env(monkeypatch):
    """Флаг перекрывает env: SERVER_ENABLED=false + --backend → true."""
    monkeypatch.setenv("SERVER_ENABLED", "false")
    app._apply_env_overrides(app._parse_args(["--backend"]))
    import os

    assert os.environ["SERVER_ENABLED"] == "true"


# ── main(): диспетчеризация роли ─────────────────────────────────────────────


@pytest.mark.pure
def test_main_both_disabled_clean_exit(monkeypatch, _pin_role_env):
    """Ни SERVER, ни WORKER → НЕ ошибка: чистый выход (None), без запуска."""
    calls = []
    monkeypatch.setattr(app, "_run_server", lambda c, a: calls.append("server"))
    monkeypatch.setattr(app.asyncio, "run", lambda c: calls.append("worker"))
    assert app.main(["--no-backend", "--no-worker"]) is None
    assert calls == []


@pytest.mark.pure
def test_main_dispatches_to_server(monkeypatch, _pin_role_env):
    """server_enabled → _run_server, worker-ветку не трогаем."""
    calls = []
    monkeypatch.setattr(app, "_run_server", lambda c, a: calls.append("server"))
    monkeypatch.setattr(app.asyncio, "run", lambda c: calls.append("worker"))
    app.main(["--backend", "--no-worker"])
    assert calls == ["server"]


@pytest.mark.pure
def test_main_pure_worker_runs_lifespan(monkeypatch, _pin_role_env):
    """Только worker → НЕ _run_server, а asyncio.run(_run_worker)."""
    calls = []
    monkeypatch.setattr(app, "_run_server", lambda c, a: calls.append("server"))

    def fake_run(coro):
        calls.append("worker")
        coro.close()  # не оставляем «coroutine never awaited»

    monkeypatch.setattr(app.asyncio, "run", fake_run)
    app.main(["--no-backend", "--worker"])
    assert calls == ["worker"]


@pytest.mark.pure
def test_main_pure_worker_hot_reload_branch(monkeypatch, _pin_role_env):
    """Только worker + hot-reload → watch-супервизор, НЕ прямой asyncio.run."""
    calls = []
    monkeypatch.setattr(app, "_run_worker_hot_reload", lambda: calls.append("watch"))
    monkeypatch.setattr(app.asyncio, "run", lambda c: calls.append("worker"))
    app.main(["--no-backend", "--worker", "--hot-reload"])
    assert calls == ["watch"]


@pytest.mark.pure
def test_run_worker_hot_reload_spawns_no_reload_child(monkeypatch):
    """_run_worker_hot_reload watch'ит src/ и рестартует worker уже с --no-hot-reload."""
    rec = {}
    monkeypatch.setitem(
        sys.modules, "watchfiles",
        types.SimpleNamespace(run_process=lambda *a, **k: rec.update(paths=a, target=k["target"])),
    )
    app._run_worker_hot_reload()
    assert rec["paths"] and rec["paths"][0].endswith("/src")
    assert "--worker" in rec["target"]
    assert "--no-backend" in rec["target"]
    assert "--no-hot-reload" in rec["target"]


# ── _run_server: reload vs processes ─────────────────────────────────────────


@pytest.mark.pure
def test_run_server_hot_reload_branch(monkeypatch):
    """server_hot_reload=true → uvicorn reload=True, workers НЕ передаётся."""
    rec = {}
    monkeypatch.setitem(
        sys.modules, "uvicorn",
        types.SimpleNamespace(run=lambda *a, **k: rec.update(a=a, k=k)),
    )
    cfg = _fake_config(server_hot_reload=True, server_processes=4)
    app._run_server(cfg, app._parse_args([]))
    assert rec["k"].get("reload") is True
    assert "workers" not in rec["k"]


@pytest.mark.pure
def test_run_server_processes_branch(monkeypatch):
    """server_hot_reload=false → uvicorn workers=N, reload НЕ передаётся."""
    rec = {}
    monkeypatch.setitem(
        sys.modules, "uvicorn",
        types.SimpleNamespace(run=lambda *a, **k: rec.update(a=a, k=k)),
    )
    cfg = _fake_config(server_hot_reload=False, server_processes=4)
    app._run_server(cfg, app._parse_args([]))
    assert rec["k"].get("workers") == 4
    assert "reload" not in rec["k"]


@pytest.mark.pure
def test_run_server_cli_overrides_config(monkeypatch):
    """--host/--port/--processes перекрывают значения config."""
    rec = {}
    monkeypatch.setitem(
        sys.modules, "uvicorn",
        types.SimpleNamespace(run=lambda *a, **k: rec.update(a=a, k=k)),
    )
    cfg = _fake_config(server_host="127.0.0.1", server_port=12200, server_processes=1)
    args = app._parse_args(["--host", "0.0.0.0", "--port", "9", "--processes", "7"])
    app._run_server(cfg, args)
    assert rec["k"]["host"] == "0.0.0.0"
    assert rec["k"]["port"] == 9
    assert rec["k"]["workers"] == 7


# ── _run_worker: scope воркера ───────────────────────────────────────────────


@pytest.mark.pure
async def test_run_worker_configures_scope(monkeypatch):
    """_run_worker форсит тикер через configure_worker с scope/ручками из config."""
    rec = {}
    from src.core import scheduler

    monkeypatch.setattr(scheduler, "configure_worker", lambda **k: rec.update(k))
    monkeypatch.setattr("src.apps.app.modules.build_modules", lambda: [])

    class _Boom(Exception):
        pass

    import src.core.app_factory as af

    def _boom(**_):
        raise _Boom

    monkeypatch.setattr(af, "create_app", _boom)

    cfg = _fake_config(
        worker_modules_set=frozenset({"alpha"}),
        worker_max_concurrent_runs=3, worker_tick_seconds=9,
    )
    with pytest.raises(_Boom):
        await app._run_worker(cfg)
    assert rec == {"modules": frozenset({"alpha"}), "max_concurrent": 3, "tick": 9}


# ── подкоманда migrate ───────────────────────────────────────────────────────


@pytest.mark.pure
def test_parse_no_command_is_run():
    """Без подкоманды → command=None (режим запуска)."""
    assert app._parse_args([]).command is None
    assert app._parse_args(["--backend"]).command is None


@pytest.mark.pure
def test_parse_migrate_default_action_is_check():
    a = app._parse_args(["migrate"])
    assert a.command == "migrate"
    assert a.action == "check"


@pytest.mark.pure
def test_parse_migrate_upgrade():
    a = app._parse_args(["migrate", "upgrade"])
    assert a.command == "migrate"
    assert a.action == "upgrade"


@pytest.mark.pure
def test_parse_migrate_rejects_unknown_action():
    with pytest.raises(SystemExit):
        app._parse_args(["migrate", "nope"])


@pytest.mark.pure
def test_main_dispatches_to_mcp_stdio(monkeypatch):
    """`--mcp-stdio` → run_mcp_stdio, минуя server/worker и role-env."""
    calls = []
    monkeypatch.setattr(app, "_run_server", lambda c, a: calls.append("server"))
    monkeypatch.setattr(app.asyncio, "run", lambda c: calls.append("worker"))
    monkeypatch.setitem(
        sys.modules, "src.apps.app.mcp_stdio",
        types.SimpleNamespace(run_mcp_stdio=lambda cfg: calls.append("mcp-stdio")),
    )
    import src.core.config as cfg_mod

    monkeypatch.setattr(cfg_mod, "Config", lambda: types.SimpleNamespace())
    assert app.main(["--mcp-stdio"]) is None
    assert calls == ["mcp-stdio"]


@pytest.mark.pure
def test_main_dispatches_to_migrate(monkeypatch):
    """`migrate` → asyncio.run(_run_migrate), без запуска сервера/воркера."""
    calls = []
    monkeypatch.setattr(app, "_run_server", lambda c, a: calls.append("server"))

    def fake_run(coro):
        calls.append("migrate")
        coro.close()
        return 0

    monkeypatch.setattr(app.asyncio, "run", fake_run)
    assert app.main(["migrate", "upgrade"]) == 0
    assert calls == ["migrate"]
