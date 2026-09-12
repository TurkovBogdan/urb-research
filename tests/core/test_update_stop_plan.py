"""What the updater decides to stop, from records plus a process table — and what it refuses.

Every table here is synthetic and nothing is signalled: these are the rules that decide whether a
whole process group may be killed at once, and the cost of getting them wrong is the operator's
shell, a neighbouring install or the coding agent's own session. The shapes are the real ones
observed on the developer machine (`RESEARCH@f4f6614217`, `NOTE@c8d020515d`).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.core.process_registry import ProcessRecord, RecordState
from src.core.process_table import Process
from src.core.update import (
    MATCH_RECORDED,
    MATCH_UNREGISTERED,
    ForeignProcesses,
    OwnIdentity,
    StopPlan,
    UnregisteredProcesses,
    UpdaterInsideInstall,
    plan_stop,
)

CHECKOUT = Path("/srv/urb-research")
OTHER_INSTALL = Path("/srv/urb-research-stable")

AGENT_SESSION_ARGV = (
    "/opt/claude-agent-sdk/claude",
    "--mcp-config",
    '{"urb-research-dev":{"args":["run","--directory","/srv/urb-research","python",'
    '"src/app.py","--mcp-stdio"]}}',
)

UPDATER_PID = 900
UPDATER_GROUP = 900


def process(
    pid: int,
    argv: str | tuple[str, ...],
    *,
    ppid: int = 1,
    pgid: int | None = None,
    cwd: Path | None = CHECKOUT,
    start_time: float = 1000.0,
) -> Process:
    return Process(
        pid=pid,
        ppid=ppid,
        pgid=pid if pgid is None else pgid,
        start_time=start_time,
        argv=tuple(argv.split()) if isinstance(argv, str) else argv,
        cwd=cwd,
    )


def record(
    pid: int,
    *,
    pgid: int | None = None,
    role: str = "backend",
    checkout: Path = CHECKOUT,
    start_time: float = 1000.0,
    argv: str = "python src/app.py --backend",
) -> ProcessRecord:
    return ProcessRecord(
        pid=pid,
        start_time=start_time,
        ppid=1,
        pgid=pid if pgid is None else pgid,
        sid=pid if pgid is None else pgid,
        role=role,
        hot_reload=False,
        port=12200,
        app_env="prod",
        checkout=str(checkout),
        argv=tuple(argv.split()),
        written_at="2026-09-13 10:00:00",
    )


def own(*, pid: int = UPDATER_PID, pgid: int | None = UPDATER_GROUP, ancestors=()) -> OwnIdentity:
    return OwnIdentity(pid=pid, pgid=pgid, ancestors=frozenset(ancestors))


def plan(
    records: list[tuple[ProcessRecord, RecordState]],
    table: list[Process],
    *,
    identity: OwnIdentity | None = None,
    stop_unregistered: bool = False,
) -> StopPlan:
    return plan_stop(
        records,
        table,
        checkout=CHECKOUT,
        own=identity or own(),
        stop_unregistered=stop_unregistered,
    )


def verified(*records: ProcessRecord) -> list[tuple[ProcessRecord, RecordState]]:
    return [(one, RecordState.VERIFIED) for one in records]


def group_pgids(made: StopPlan) -> list[int]:
    return [group.pgid for group in made.groups]


# ── a group that is provably ours is stopped as one ──────────────────────────

@pytest.mark.pure
def test_a_backend_spawned_into_its_own_session_is_stopped_as_a_group():
    """What the MCP shim and the updater both produce: `start_new_session=True`, so the backend
    leads its own group and everything it spawns is in it."""
    backend = process(100, "python src/app.py --backend", pgid=100)
    worker_pool = process(101, "python -c worker_pool", ppid=100, pgid=100)
    grandchild = process(102, "python -c parser", ppid=101, pgid=100)

    made = plan(verified(record(100)), [backend, worker_pool, grandchild])

    assert group_pgids(made) == [100]
    assert sorted(made.pids) == [100, 101, 102]
    assert made.singles == ()


@pytest.mark.pure
def test_the_readme_launch_is_stopped_as_a_group_with_uv_as_its_leader():
    """`uv run python src/app.py --backend --worker` from a terminal: the job's leader is `uv`,
    which is not recorded — it is our chain to the leader, and it forwards TERM to python."""
    wrapper = process(100, "uv run python src/app.py --backend --worker", pgid=100)
    backend = process(101, "/srv/urb-research/.venv/bin/python3 src/app.py --backend", ppid=100, pgid=100)
    child = process(102, "python -c scheduler", ppid=101, pgid=100)

    made = plan(verified(record(101, pgid=100)), [wrapper, backend, child])

    assert group_pgids(made) == [100]
    assert sorted(made.pids) == [100, 101, 102]


@pytest.mark.pure
def test_two_installs_of_one_checkout_are_both_stopped():
    """A dev profile and a prod profile out of the same clone share the venv being replaced."""
    dev = process(100, "python src/app.py --backend", pgid=100)
    prod = process(200, "python src/app.py --backend --worker", pgid=200)

    made = plan(verified(record(100), record(200)), [dev, prod])

    assert group_pgids(made) == [100, 200]


# ── the About-page button: the updater's own parent is a target ───────────────

@pytest.mark.pure
def test_the_button_stops_the_backend_that_spawned_the_updater():
    """The defect this design closes: the in-app updater is a child of the backend, and the
    ancestor veto used to protect it — so the migration ran beside a live writer and the health
    probe was answered by the old process, which printed «update complete»."""
    backend = process(200, "python src/app.py --backend", pgid=200)
    script = process(300, "bash update.sh", ppid=200, pgid=UPDATER_GROUP)
    wrapper = process(301, "uv run python src/app.py update", ppid=300, pgid=UPDATER_GROUP)
    updater = process(UPDATER_PID, "python src/app.py update", ppid=301, pgid=UPDATER_GROUP)

    made = plan(
        verified(record(200)),
        [backend, script, wrapper, updater],
        identity=own(ancestors={301, 300, 200}),
    )

    assert group_pgids(made) == [200]
    assert made.pids == [200]
    assert UPDATER_PID not in made.pids


# ── a group with a stranger in it is stopped pid by pid ──────────────────────

@pytest.mark.pure
def test_a_group_holding_the_agent_session_is_never_signalled_as_a_group():
    """The live shape of this machine: the agent session and both MCP shims sit in the terminal's
    process group. A group kill computed from the table would be suicide."""
    agent = process(50, AGENT_SESSION_ARGV, pgid=50)
    shim = process(51, "python src/app.py --mcp-stdio", ppid=50, pgid=50)
    backend = process(100, "python src/app.py --backend", ppid=51, pgid=50)

    made = plan(verified(record(100, pgid=50)), [agent, shim, backend])

    assert made.groups == ()
    assert made.pids == [100]
    assert any("also holds" in note for note in made.notes)
    assert any("claude" in note for note in made.notes)


@pytest.mark.pure
def test_a_group_holding_the_shell_that_started_the_updater_falls_back_to_pids():
    launcher = process(50, "bash run.sh", pgid=50)
    backend = process(100, "python src/app.py --backend", ppid=50, pgid=50)

    made = plan(
        verified(record(100, pgid=50)),
        [launcher, backend],
        identity=own(ancestors={50}),
    )

    assert made.groups == ()
    assert made.pids == [100]
    assert any("bash run.sh" in note for note in made.notes)


@pytest.mark.pure
def test_the_updaters_own_group_is_never_a_group_target():
    backend = process(100, "python src/app.py --backend", pgid=UPDATER_GROUP)

    made = plan(verified(record(100, pgid=UPDATER_GROUP)), [backend])

    assert made.groups == ()
    assert any("the updater's own" in note for note in made.notes)


@pytest.mark.pure
def test_descendants_are_stopped_deepest_first():
    """A parent signalled first orphans its children, and an orphan reparents out of every walk."""
    launcher = process(50, "bash run.sh", pgid=50)
    backend = process(100, "python src/app.py --backend", ppid=50, pgid=50)
    child = process(101, "python -c worker", ppid=100, pgid=50)
    grandchild = process(102, "python -c parser", ppid=101, pgid=50)

    made = plan(
        verified(record(100, pgid=50)),
        [launcher, backend, child, grandchild],
        identity=own(ancestors={50}),
    )

    assert made.pids == [102, 101, 100]
    assert made.singles[-1].matched_as == MATCH_RECORDED


@pytest.mark.pure
def test_a_platform_without_process_groups_is_stopped_pid_by_pid():
    """Windows: `pgid` is None in the record and in the table, and nothing may raise over it."""
    backend = Process(
        pid=100, ppid=1, pgid=None, start_time=1000.0, argv=("python", "src/app.py"), cwd=CHECKOUT
    )
    groupless = replace(record(100), pgid=None, sid=None)

    made = plan(verified(groupless), [backend])

    assert made.groups == ()
    assert made.pids == [100]
    assert any("no process group" in note for note in made.notes)


# ── refusals ─────────────────────────────────────────────────────────────────

@pytest.mark.pure
def test_a_record_of_another_user_refuses_the_update():
    """macOS answers nothing about another account's process, so it can be neither read nor
    signalled — and migrating beside a live writer is the one outcome worth refusing over."""
    made = plan([(record(100), RecordState.FOREIGN)], [])

    assert made.foreign
    with pytest.raises(ForeignProcesses) as refusal:
        made.refuse_if_unsafe()
    assert "another user" in str(refusal.value)


@pytest.mark.pure
def test_the_updater_inside_the_installs_own_group_refuses():
    backend = process(UPDATER_GROUP, "python src/app.py --backend", pgid=UPDATER_GROUP)

    made = plan(verified(record(UPDATER_GROUP, pgid=UPDATER_GROUP)), [backend])

    with pytest.raises(UpdaterInsideInstall):
        made.refuse_if_unsafe()


@pytest.mark.pure
def test_an_unregistered_process_of_this_checkout_refuses_instead_of_being_killed():
    """The sweep's key is `cwd` plus an argv token — the evidence the research showed to be
    unreliable per OS and rewritable by the process. A find is the operator's decision."""
    unrecorded = process(100, "python src/app.py --backend", pgid=100)

    made = plan([], [unrecorded])

    assert made.is_empty
    assert [stray.process.pid for stray in made.strays] == [100]
    with pytest.raises(UnregisteredProcesses) as refusal:
        made.refuse_if_unsafe()
    assert "--stop-unregistered" in str(refusal.value)


@pytest.mark.pure
def test_stop_unregistered_turns_the_strays_into_pid_targets():
    unrecorded = process(100, "python src/app.py --backend", pgid=100)

    made = plan([], [unrecorded], stop_unregistered=True)

    assert made.strays == ()
    assert made.pids == [100]
    assert made.singles[0].matched_as == MATCH_UNREGISTERED
    made.refuse_if_unsafe()


@pytest.mark.pure
def test_a_stale_record_is_reported_and_dropped_not_signalled():
    made = plan([(record(100), RecordState.STALE)], [])

    assert [stale.pid for stale in made.stale] == [100]
    assert made.is_empty
    assert "stale record" in made.describe()
    made.refuse_if_unsafe()


@pytest.mark.pure
def test_a_record_from_another_checkout_is_ignored():
    made = plan([(record(100, checkout=OTHER_INSTALL), RecordState.OTHER_CHECKOUT)], [])

    assert [elsewhere.pid for elsewhere in made.elsewhere] == [100]
    assert made.is_empty
    assert "another checkout" in made.describe()


@pytest.mark.pure
def test_no_records_and_no_strays_is_nothing_to_stop():
    unrelated = process(500, "python -c something_else", cwd=None)

    made = plan([], [unrelated])

    assert made.is_empty
    assert made.strays == ()
    assert "nothing to stop" in made.describe()
    made.refuse_if_unsafe()


@pytest.mark.pure
def test_a_neighbouring_install_is_neither_a_target_nor_a_stray():
    stable = process(
        700,
        "/srv/urb-research-stable/.venv/bin/python3 /srv/urb-research-stable/src/app.py --backend",
        pgid=700,
        cwd=OTHER_INSTALL,
    )

    made = plan([], [stable])

    assert made.is_empty
    assert made.strays == ()


@pytest.mark.pure
def test_a_recorded_group_swallows_what_the_sweep_would_have_found():
    """Everything the sweep sees is already covered by the group, so nothing is left to refuse."""
    backend = process(100, "python src/app.py --backend", pgid=100)
    reload_child = process(101, "python -c multiprocessing --multiprocessing-fork", ppid=100, pgid=100)

    made = plan(verified(record(100)), [backend, reload_child])

    assert made.strays == ()
    made.refuse_if_unsafe()
