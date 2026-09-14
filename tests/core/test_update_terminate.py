"""`update.execute_stop` against real processes — the only part of the stop that cannot be read.

Every process signalled here is a decoy this test spawned itself, and every plan is built from
those pids alone: nothing is ever selected from the live process table, so the suite can never
reach a neighbouring install, an MCP shim or the agent session. A group plan is only ever built
for a decoy started in its own session, and the plan's own identity is this process's real one —
so even a mistake in the group rules would protect pytest, not signal it. Which processes a real
update would pick is proven separately, on synthetic tables (`test_update_stop_plan.py`).

What it establishes: a process group dies whole (including a grandchild a TERM to the leader
would orphan), a stopped process is resumed so it can handle TERM at all, a group that ignores
TERM is killed anyway, an undelivered signal is a refusal rather than success, and a zombie
counts as gone.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import pytest

from src.core.process_table import process_is_running, process_start_time, read_process_table
from src.core.update import (
    MATCH_GROUP_MEMBER,
    MATCH_RECORDED,
    GroupStop,
    OwnIdentity,
    ProcessesSurvived,
    StopPlan,
    StopTarget,
    execute_stop,
)
from src.core.update import stop as stop_module

CHECKOUT = Path("/srv/urb-research")
READY = "ready"

OBEYS_TERM = f"import time\nprint('{READY}', flush=True)\ntime.sleep(60)\n"
IGNORES_TERM = (
    "import signal, time\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    f"print('{READY}', flush=True)\n"
    "time.sleep(60)\n"
)
SPAWNS_A_CHILD = (
    "import subprocess, sys, time\n"
    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
    "print(child.pid, flush=True)\n"
    "time.sleep(60)\n"
)
STOPS_ITSELF = (
    "import os, signal, time\n"
    f"print('{READY}', flush=True)\n"
    "os.kill(os.getpid(), signal.SIGSTOP)\n"
    "time.sleep(60)\n"
)

GRACE = 0.5
PATIENCE = 10.0


class Decoys:
    """Children this test owns: spawned on demand, reaped on the way out."""

    def __init__(self) -> None:
        self._spawned: list[subprocess.Popen] = []
        self._grandchildren: list[int] = []

    def spawn(self, script: str, *, own_session: bool = False) -> subprocess.Popen:
        process = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=own_session,
        )
        self._spawned.append(process)
        announced = process.stdout.readline().strip()
        if announced != READY:
            self._grandchildren.append(int(announced))
        return process

    @property
    def grandchildren(self) -> list[int]:
        return list(self._grandchildren)

    def pid_plan(self, *processes: subprocess.Popen) -> StopPlan:
        """A per-pid plan, deepest first — the shape used when a group cannot be trusted."""
        return StopPlan(
            checkout=CHECKOUT,
            own=self._own_identity(),
            singles=tuple(self._target(pid, MATCH_RECORDED) for pid in self._pids(*processes)),
        )

    def group_plan(self, leader: subprocess.Popen) -> StopPlan:
        """The group of a decoy that was given its own session — its members are its own tree."""
        pgid = os.getpgid(leader.pid)
        assert pgid == leader.pid, "a group plan is only ever built for a session leader"
        assert pgid != os.getpgrp(), "never a group this test runner is in"
        members = [self._target(leader.pid, MATCH_RECORDED)]
        members += [self._target(pid, MATCH_GROUP_MEMBER) for pid in self._grandchildren]
        return StopPlan(
            checkout=CHECKOUT,
            own=self._own_identity(),
            groups=(GroupStop(pgid=pgid, record_pid=leader.pid, members=tuple(members)),),
        )

    def clean_up(self) -> None:
        for pid in self._grandchildren:
            with suppress(ProcessLookupError, PermissionError):
                os.kill(pid, signal.SIGKILL)
        for process in self._spawned:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()

    def _pids(self, *processes: subprocess.Popen) -> list[int]:
        owned = {process.pid for process in self._spawned} | set(self._grandchildren)
        pids = [process.pid for process in processes]
        assert set(pids) <= owned
        return pids

    def _target(self, pid: int, matched_as: str) -> StopTarget:
        started = process_start_time(pid)
        assert started is not None, f"decoy {pid} is already gone"
        return StopTarget(
            pid=pid, start_time=started, command_line=f"decoy {pid}", matched_as=matched_as
        )

    def _own_identity(self) -> OwnIdentity:
        return OwnIdentity.of_this_process(read_process_table())


@pytest.fixture
def decoys():
    owned = Decoys()
    try:
        yield owned
    finally:
        owned.clean_up()


@pytest.mark.pure
def test_a_whole_process_group_dies_including_a_grandchild(decoys):
    """A TERM to the leader alone would leave the grandchild running and reparented to init —
    the membership is what makes the stop complete."""
    leader = decoys.spawn(SPAWNS_A_CHILD, own_session=True)
    grandchild = decoys.grandchildren[0]

    stopped = execute_stop(decoys.group_plan(leader), term_grace=PATIENCE)

    assert sorted(stopped) == sorted([leader.pid, grandchild])
    assert leader.wait(timeout=PATIENCE) == -signal.SIGTERM
    assert process_is_running(grandchild) is False
    assert process_is_running(os.getpid()) is True


@pytest.mark.pure
def test_a_stopped_process_is_resumed_so_it_can_handle_term(decoys):
    """Ctrl-Z in the operator's terminal: without the SIGCONT of systemd's ladder the process
    would sit on the queued TERM until the grace window expired and take a KILL instead."""
    suspended = decoys.spawn(STOPS_ITSELF, own_session=True)

    execute_stop(decoys.group_plan(suspended), term_grace=PATIENCE)

    assert suspended.wait(timeout=PATIENCE) == -signal.SIGTERM


@pytest.mark.pure
def test_a_group_that_ignores_term_is_killed_after_the_grace_window(decoys):
    stubborn = decoys.spawn(IGNORES_TERM, own_session=True)

    execute_stop(decoys.group_plan(stubborn), term_grace=GRACE, kill_grace=PATIENCE)

    assert stubborn.wait(timeout=PATIENCE) == -signal.SIGKILL


@pytest.mark.pure
def test_the_pid_path_stops_every_target(decoys):
    obedient = decoys.spawn(OBEYS_TERM)
    stubborn = decoys.spawn(IGNORES_TERM)

    stopped = execute_stop(
        decoys.pid_plan(obedient, stubborn), term_grace=GRACE, kill_grace=PATIENCE
    )

    assert stopped == [obedient.pid, stubborn.pid]
    assert obedient.wait(timeout=PATIENCE) == -signal.SIGTERM
    assert stubborn.wait(timeout=PATIENCE) == -signal.SIGKILL


@pytest.mark.pure
def test_a_survivor_refuses_the_update_instead_of_reporting_success(decoys, monkeypatch):
    """Signals that never land (another user's process) leave a writer running, and the very next
    step rewrites the schema — so liveness, not a return code, decides."""
    survivor = decoys.spawn(OBEYS_TERM)
    monkeypatch.setattr(stop_module, "_signal_pid", lambda target, sent: None)

    with pytest.raises(ProcessesSurvived) as refusal:
        execute_stop(decoys.pid_plan(survivor), term_grace=GRACE, kill_grace=GRACE)

    assert str(survivor.pid) in str(refusal.value)
    assert survivor.poll() is None


@pytest.mark.pure
def test_a_pid_whose_process_is_no_longer_the_planned_one_is_left_alone(decoys):
    """The number is reused; the plan is not. A start time that no longer matches means the
    planned process is gone, so the stranger now holding its pid is neither signalled nor waited
    for — which is why every target carries a start time at all."""
    stranger = decoys.spawn(OBEYS_TERM)
    planned_long_ago = StopPlan(
        checkout=CHECKOUT,
        own=decoys.pid_plan(stranger).own,
        singles=(
            StopTarget(
                pid=stranger.pid,
                start_time=1.0,
                command_line="a process that exited long ago",
                matched_as=MATCH_RECORDED,
            ),
        ),
    )

    execute_stop(planned_long_ago, term_grace=GRACE, kill_grace=GRACE)

    assert stranger.poll() is None
    assert process_is_running(stranger.pid) is True


@pytest.mark.pure
@pytest.mark.skipif(not hasattr(os, "waitid"), reason="macOS builds of CPython omit os.waitid")
def test_an_unreaped_zombie_counts_as_gone(decoys):
    """The updater is the parent of nothing it kills, but a test is — and a zombie holds no
    files, writes nothing and would otherwise stall the verification forever.

    Only the way the zombie is *made* is Linux-only: reaching an exited child without reaping it
    needs `WNOWAIT`. What is asserted holds on every platform the reader supports."""
    decoy = decoys.spawn(OBEYS_TERM)
    decoy.kill()
    os.waitid(os.P_PID, decoy.pid, os.WEXITED | os.WNOWAIT)

    assert process_is_running(decoy.pid) is False
    assert execute_stop(decoys.pid_plan(decoy), term_grace=GRACE) == [decoy.pid]
