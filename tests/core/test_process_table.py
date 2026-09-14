"""The live process table — the one part of the stop that cannot be read off a fixture.

Nothing here signals anything: the table is read, and the only process it is asserted about is
the test runner itself. The procfs reader this replaced was Linux-only and crashed a macOS
install (`os.listdir("/proc")`), so what these tests are really for is proving the reader works
on whatever the operator runs — they must pass unchanged on Linux and on macOS.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psutil
import pytest

from src.core import process_table
from src.core.process_table import (
    Liveness,
    process_argv,
    process_is_running,
    process_liveness,
    process_start_time,
    read_process_table,
)

REAPED = "import sys\nsys.exit(0)\n"


def a_dead_pid() -> int:
    """A pid this test owned and reaped, so nothing else can be answering for it yet."""
    child = subprocess.Popen([sys.executable, "-c", REAPED])
    child.wait()
    return child.pid


@pytest.mark.pure
def test_reads_this_process_out_of_the_live_table():
    table = {entry.pid: entry for entry in read_process_table()}

    own = table[os.getpid()]
    assert own.ppid == os.getppid()
    assert own.pgid == os.getpgrp()
    assert own.cwd == Path.cwd().resolve()
    assert own.argv and "python" in own.argv[0]


@pytest.mark.pure
def test_the_table_records_when_each_process_started():
    """The identity half of a pid: without it a survivor and a stranger that inherited the number
    are the same row."""
    table = {entry.pid: entry for entry in read_process_table()}

    own = table[os.getpid()]
    assert own.start_time == pytest.approx(
        psutil.Process(os.getpid()).create_time(), abs=process_table.START_TIME_TOLERANCE_SECONDS
    )


@pytest.mark.pure
def test_process_is_running_for_this_process_and_not_for_a_reaped_one():
    assert process_is_running(os.getpid()) is True
    assert process_is_running(a_dead_pid()) is False


@pytest.mark.pure
def test_a_start_time_that_does_not_match_reads_as_gone():
    """How pid reuse is caught: the number is alive, but it is not the process that was planned."""
    assert process_liveness(os.getpid(), start_time=1.0) is Liveness.GONE
    assert process_is_running(os.getpid(), start_time=1.0) is False


@pytest.mark.pure
def test_a_process_this_user_may_not_read_is_alive_not_gone(monkeypatch: pytest.MonkeyPatch):
    """macOS refuses another account's process entirely. Rounding that down to «gone» is how a
    migration ends up running beside a live writer, so it is its own answer."""
    monkeypatch.setattr(
        psutil.Process, "status", lambda self: (_ for _ in ()).throw(psutil.AccessDenied(self.pid))
    )

    assert process_liveness(os.getpid()) is Liveness.FOREIGN
    assert process_is_running(os.getpid()) is True


@pytest.mark.pure
def test_process_start_time_is_none_for_a_process_that_is_gone():
    assert process_start_time(os.getpid()) is not None
    assert process_start_time(a_dead_pid()) is None


@pytest.mark.pure
def test_process_argv_is_one_string_and_none_when_the_process_is_gone():
    assert "python" in (process_argv(os.getpid()) or "")
    assert process_argv(a_dead_pid()) is None
