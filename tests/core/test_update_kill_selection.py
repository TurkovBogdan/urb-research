"""Kill selection for `app.py update`: what it picks, and everything it must never touch.

The process table is synthetic on purpose — the veto rules have to be provable without spawning
anything, because the failure mode is killing the agent session or a second install.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.core import update
from src.core.update import (
    MATCH_DESCENDANT,
    MATCH_LAUNCHER,
    KillPlan,
    Process,
    parse_proc_stat,
    select_kill_targets,
    terminate,
)

CHECKOUT = Path("/srv/urb-research")
OTHER_INSTALL = Path("/srv/urb-research-stable")

AGENT_SESSION_ARGV = (
    "/opt/claude-agent-sdk/claude",
    "--mcp-config",
    '{"urb-research-dev":{"args":["run","--directory","/srv/urb-research","python",'
    '"src/app.py","--mcp-stdio"]}}',
)


def process(
    pid: int,
    argv: str | tuple[str, ...],
    *,
    ppid: int = 1,
    pgid: int | None = None,
    cwd: Path | None = CHECKOUT,
) -> Process:
    return Process(
        pid=pid,
        ppid=ppid,
        pgid=pid if pgid is None else pgid,
        argv=tuple(argv.split()) if isinstance(argv, str) else argv,
        cwd=cwd,
    )


def select(*processes: Process, own_pid: int = -1, own_process_group: int = -1) -> list[int]:
    targets = select_kill_targets(
        processes,
        checkout=CHECKOUT,
        own_pid=own_pid,
        own_process_group=own_process_group,
    )
    return [target.process.pid for target in targets]


# ── what must be stopped ─────────────────────────────────────────────────────

@pytest.mark.pure
def test_selects_backend_launcher_and_its_uv_wrapper():
    wrapper = process(100, "uv run python src/app.py --backend --hot-reload")
    launcher = process(101, "/srv/urb-research/.venv/bin/python3 src/app.py --backend", ppid=100)

    assert select(wrapper, launcher) == [100, 101]


@pytest.mark.pure
def test_selects_a_worker_that_binds_no_port():
    worker = process(100, "/srv/urb-research/.venv/bin/python3 src/app.py --worker")

    assert select(worker) == [100]


@pytest.mark.pure
def test_selects_a_launch_whose_role_comes_from_env():
    bare = process(100, "python src/app.py")

    assert select(bare) == [100]


@pytest.mark.pure
def test_selects_an_absolute_entry_path_of_this_checkout():
    absolute = process(100, "python /srv/urb-research/src/app.py --backend --worker")

    assert select(absolute) == [100]


@pytest.mark.pure
def test_selects_the_uvicorn_form():
    served_by_uvicorn = process(100, "/srv/urb-research/.venv/bin/uvicorn src.apps.app.server:app")

    assert select(served_by_uvicorn) == [100]


@pytest.mark.pure
def test_collects_descendants_the_argv_rule_cannot_see():
    launcher = process(100, "uv run python src/app.py --backend --hot-reload")
    reload_supervisor = process(101, "python src/app.py --backend --hot-reload", ppid=100)
    reload_child = process(
        102,
        "python -c from_multiprocessing.spawn_import_spawn_main --multiprocessing-fork",
        ppid=101,
    )
    resource_tracker = process(103, "python -c from_multiprocessing.resource_tracker", ppid=101)
    unrelated = process(200, "python -c something_else", ppid=1, cwd=None)

    assert select(launcher, reload_supervisor, reload_child, resource_tracker, unrelated) == [
        100,
        101,
        102,
        103,
    ]


@pytest.mark.pure
def test_descendant_carries_its_parent_in_the_reason():
    launcher = process(100, "python src/app.py --backend")
    child = process(101, "python -c worker_pool", ppid=100)

    targets = select_kill_targets(
        [launcher, child], checkout=CHECKOUT, own_pid=-1, own_process_group=-1
    )

    assert [(t.process.pid, t.matched_as, t.parent_pid) for t in targets] == [
        (100, MATCH_LAUNCHER, None),
        (101, MATCH_DESCENDANT, 100),
    ]


# ── what must never be stopped ───────────────────────────────────────────────

@pytest.mark.pure
def test_vetoes_another_install_whose_argv_names_its_own_app_py():
    stable_backend = process(
        100,
        "/srv/urb-research-stable/.venv/bin/python3 /srv/urb-research-stable/src/app.py --backend",
        cwd=OTHER_INSTALL,
    )

    assert select(stable_backend) == []


@pytest.mark.pure
def test_vetoes_an_install_that_shares_the_relative_entry_path():
    stable_backend = process(100, "python src/app.py --backend", cwd=OTHER_INSTALL)

    assert select(stable_backend) == []


@pytest.mark.pure
def test_vetoes_the_mcp_shim_of_this_very_checkout():
    shim_wrapper = process(100, "uv run --directory /srv/urb-research python src/app.py --mcp-stdio")
    shim = process(101, "/srv/urb-research/.venv/bin/python3 src/app.py --mcp-stdio", ppid=100)

    assert select(shim_wrapper, shim) == []


@pytest.mark.pure
def test_vetoes_the_agent_session_that_carries_app_py_in_its_own_arguments():
    agent = process(100, AGENT_SESSION_ARGV)

    assert select(agent) == []


@pytest.mark.pure
def test_veto_reaches_descendants_too():
    launcher = process(100, "python src/app.py --backend")
    shim_spawned_below_it = process(101, "python src/app.py --mcp-stdio", ppid=100)
    agent_below_it = process(102, AGENT_SESSION_ARGV, ppid=100)

    assert select(launcher, shim_spawned_below_it, agent_below_it) == [100]


@pytest.mark.pure
def test_never_selects_the_updater_itself():
    updater = process(100, "python src/app.py update")
    migration = process(101, "python src/app.py migrate upgrade", ppid=100)

    assert select(updater, migration) == []


@pytest.mark.pure
def test_excludes_own_pid_and_own_process_group():
    own = process(100, "python src/app.py --backend", pgid=100)
    sibling_in_own_group = process(101, "python src/app.py --worker", pgid=100)
    elsewhere = process(200, "python src/app.py --backend", pgid=200)

    assert select(own, sibling_in_own_group, elsewhere, own_pid=100, own_process_group=100) == [200]


@pytest.mark.pure
def test_ignores_a_process_with_an_unreadable_cwd():
    unreadable = process(100, "python src/app.py --backend", cwd=None)

    assert select(unreadable) == []


# ── the /proc reader and the guarded kill ────────────────────────────────────

@pytest.mark.pure
def test_parse_proc_stat_survives_a_comm_with_spaces_and_parens():
    stat_line = "4242 (weird (name) here) S 4200 4100 4000 0 -1 4194560 0 0 0"

    assert parse_proc_stat(stat_line) == (4200, 4100)


@pytest.mark.pure
def test_terminate_sends_nothing_by_default(monkeypatch: pytest.MonkeyPatch):
    signalled: list[tuple[int, int]] = []
    monkeypatch.setattr(update, "_signal", lambda pid, sent: signalled.append((pid, sent)) or True)
    plan = KillPlan(
        checkout=CHECKOUT,
        targets=select_kill_targets(
            [process(100, "python src/app.py --backend")],
            checkout=CHECKOUT,
            own_pid=-1,
            own_process_group=-1,
        ),
    )

    assert plan.pids == [100]
    assert terminate(plan) == []
    assert signalled == []


@pytest.mark.pure
def test_reads_the_live_process_table_without_signalling_anything():
    table = {entry.pid: entry for entry in update.read_process_table()}

    own = table[os.getpid()]
    assert own.pgid == os.getpgrp()
    assert own.cwd == Path.cwd().resolve()
    assert own.argv and "python" in own.argv[0]
