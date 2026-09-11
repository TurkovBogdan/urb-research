"""`update.terminate` against real processes — the only part of the kill that cannot be read.

Every process signalled here is a decoy this test spawned itself (`python -c "sleep"`), and the
plan is built from those pids alone: nothing is ever selected from the live process table, so the
suite can never reach a neighbouring install, an MCP shim or the agent session. Selection is
proven separately, on a synthetic table (`test_update_kill_selection.py`).

What it establishes: TERM stops an ordinary child, the grace window is honoured, a child that
ignores TERM is killed anyway, an undelivered signal is refused rather than reported as success,
and a zombie counts as gone.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from src.core.update import selection
from src.core.update import (
    MATCH_LAUNCHER,
    KillPlan,
    KillTarget,
    Process,
    ProcessesSurvived,
    process_is_running,
    terminate,
)

CHECKOUT = Path("/srv/urb-research")
READY = "ready"

OBEYS_TERM = f"import time\nprint('{READY}', flush=True)\ntime.sleep(60)\n"
IGNORES_TERM = (
    "import signal, time\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    f"print('{READY}', flush=True)\n"
    "time.sleep(60)\n"
)

GRACE = 0.5
PATIENCE = 10.0


class Decoys:
    """Children this test owns: spawned on demand, reaped on the way out."""

    def __init__(self) -> None:
        self._spawned: list[subprocess.Popen] = []

    def spawn(self, script: str) -> subprocess.Popen:
        process = subprocess.Popen(
            [sys.executable, "-c", script], stdout=subprocess.PIPE, text=True
        )
        self._spawned.append(process)
        assert process.stdout.readline().strip() == READY
        return process

    def plan_for(self, *processes: subprocess.Popen) -> KillPlan:
        owned = {process.pid for process in self._spawned}
        assert {process.pid for process in processes} <= owned
        return KillPlan(
            checkout=CHECKOUT,
            targets=[
                KillTarget(
                    Process(pid=process.pid, ppid=os.getpid(), pgid=os.getpgrp()), MATCH_LAUNCHER
                )
                for process in processes
            ],
        )

    def clean_up(self) -> None:
        for process in self._spawned:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()


@pytest.fixture
def decoys():
    owned = Decoys()
    try:
        yield owned
    finally:
        owned.clean_up()


@pytest.mark.pure
def test_a_dry_run_leaves_a_live_process_alone(decoys):
    decoy = decoys.spawn(OBEYS_TERM)

    assert terminate(decoys.plan_for(decoy)) == []
    assert decoy.poll() is None
    assert process_is_running(decoy.pid) is True


@pytest.mark.pure
def test_term_stops_an_ordinary_process(decoys):
    decoy = decoys.spawn(OBEYS_TERM)

    signalled = terminate(decoys.plan_for(decoy), dry_run=False, grace_seconds=PATIENCE)

    assert signalled == [decoy.pid]
    assert decoy.wait(timeout=PATIENCE) == -signal.SIGTERM
    assert process_is_running(decoy.pid) is False


@pytest.mark.pure
def test_a_process_that_ignores_term_is_killed_after_the_grace_window(decoys):
    stubborn = decoys.spawn(IGNORES_TERM)

    terminate(decoys.plan_for(stubborn), dry_run=False, grace_seconds=GRACE)

    assert stubborn.wait(timeout=PATIENCE) == -signal.SIGKILL
    assert process_is_running(stubborn.pid) is False


@pytest.mark.pure
def test_the_whole_plan_is_stopped_not_just_the_first(decoys):
    obedient = decoys.spawn(OBEYS_TERM)
    stubborn = decoys.spawn(IGNORES_TERM)

    signalled = terminate(
        decoys.plan_for(obedient, stubborn), dry_run=False, grace_seconds=GRACE
    )

    assert signalled == [obedient.pid, stubborn.pid]
    assert obedient.wait(timeout=PATIENCE) == -signal.SIGTERM
    assert stubborn.wait(timeout=PATIENCE) == -signal.SIGKILL


@pytest.mark.pure
def test_a_survivor_refuses_the_update_instead_of_reporting_success(decoys, monkeypatch):
    """Signals that never land (another user's process) leave a writer running, and the very next
    step rewrites the schema — so liveness, not a return code, decides."""
    survivor = decoys.spawn(OBEYS_TERM)
    monkeypatch.setattr(selection, "_signal", lambda pid, sent: False)

    with pytest.raises(ProcessesSurvived) as refusal:
        terminate(decoys.plan_for(survivor), dry_run=False, grace_seconds=GRACE)

    assert str(survivor.pid) in str(refusal.value)
    assert survivor.poll() is None


@pytest.mark.pure
def test_an_unreaped_zombie_counts_as_gone(decoys):
    """The updater is the parent of nothing it kills, but a test is — and a zombie holds no
    files, writes nothing and would otherwise stall the verification forever."""
    decoy = decoys.spawn(OBEYS_TERM)
    decoy.kill()
    os.waitid(os.P_PID, decoy.pid, os.WEXITED | os.WNOWAIT)

    assert process_is_running(decoy.pid) is False
    assert terminate(decoys.plan_for(decoy), dry_run=False, grace_seconds=GRACE) == [decoy.pid]
