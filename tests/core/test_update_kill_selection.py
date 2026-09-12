"""The stray sweep for `app.py update`: what it finds, and everything it must never point at.

The process table is synthetic on purpose — the veto rules have to be provable without spawning
anything, because the failure mode is killing the agent session or a second install. A find of
this sweep is no longer a kill target: it is a reason for the update to refuse (exit 10), and
what gets stopped comes from the registry instead (`test_update_stop_plan.py`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core import update
from src.core.process_table import Process
from src.core.update import MATCH_DESCENDANT, MATCH_LAUNCHER, select_kill_targets

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
def test_excludes_the_updaters_own_ancestors_whatever_their_process_group():
    """`uv run` puts the updater in a new process group, so the group rule alone would not
    protect the shell that launched it — the ancestor chain is excluded by pid instead."""
    launcher_of_the_updater = process(50, "python src/app.py --backend", pgid=50)
    elsewhere = process(200, "python src/app.py --backend", pgid=200)

    targets = select_kill_targets(
        [launcher_of_the_updater, elsewhere],
        checkout=CHECKOUT,
        own_pid=100,
        own_process_group=100,
        own_ancestors={50},
    )

    assert [target.process.pid for target in targets] == [200]


@pytest.mark.pure
def test_ancestor_pids_walks_the_parent_chain():
    terminal = process(10, "bash", ppid=1)
    wrapper = process(20, "uv run python src/app.py update", ppid=10)
    updater = process(30, "python src/app.py update", ppid=20)

    assert update.ancestor_pids([terminal, wrapper, updater], 30) == {20, 10, 1}


@pytest.mark.pure
def test_ignores_a_process_with_an_unreadable_cwd():
    unreadable = process(100, "python src/app.py --backend", cwd=None)

    assert select(unreadable) == []
