"""Stopping every process of THIS install, from what those processes recorded about themselves.

`plan_stop` is a pure function — records and a process table in, a `StopPlan` out, with the reason
for every decision; `plan_live_stop` runs it against the live machine; `execute_stop` signals a
plan and proves the processes are gone. A plan is signalled only through `execute_stop`, and only
after `refuse_if_unsafe` finds nothing unaccounted for.

The unit of stopping is a **membership**, not a snapshot: a POSIX process group holds whatever its
members spawn, while a ppid walk loses a child whose parent died first, races pid reuse, and never
sees a process born after the table was read. A group is signalled only when every one of its live
members is explained by the registry — otherwise the same processes are stopped one pid at a time,
because the terminal's group can hold the operator's shell, an MCP shim or the agent session. What
the registry is and why the sweep only refuses: `AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import os
import signal
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import psutil

from src.core.app_path import project_root
from src.core.process_registry import ProcessRecord, RecordState, read_records, verify, withdraw
from src.core.process_table import (
    START_TIME_TOLERANCE_SECONDS,
    Liveness,
    Process,
    process_liveness,
    process_start_time,
    read_process_table,
)
from src.core.update.errors import UpdateRefused
from src.core.update.selection import (
    KillTarget,
    ancestor_pids,
    argv_is_vetoed,
    descendants,
    select_kill_targets,
)

# Long enough for uvicorn to finish the requests in flight: a search-backed MCP call takes
# seconds, and a KILL mid-request costs the caller its answer.
TERM_GRACE_SECONDS = 10.0
KILL_GRACE_SECONDS = 3.0
LIVENESS_POLL_SECONDS = 0.2

TERMINATE_SIGNAL = signal.SIGTERM
# Named through `getattr` because Windows has neither, and merely importing this module there must
# not raise — the update refuses that platform with a message, not a traceback.
FORCE_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)
# A member stopped with Ctrl-Z never handles TERM until it is resumed; systemd's ladder sends CONT
# for exactly that reason.
CONTINUE_SIGNAL = getattr(signal, "SIGCONT", None)

MATCH_RECORDED = "recorded"
MATCH_DESCENDANT_OF_RECORD = "descendant"
MATCH_GROUP_MEMBER = "group member"
MATCH_UNREGISTERED = "unregistered"


class ProcessesSurvived(UpdateRefused):
    """Something this checkout runs is still alive after TERM and KILL."""


class ForeignProcesses(UpdateRefused):
    """A recorded process belongs to another user — unstoppable and still able to write."""


class UpdaterInsideInstall(UpdateRefused):
    """The updater shares a process group with the install it is supposed to stop."""


class UnregisteredProcesses(UpdateRefused):
    """The table holds processes of this checkout that no record explains."""


@dataclass(frozen=True)
class StopTarget:
    pid: int
    start_time: float
    command_line: str
    matched_as: str

    def describe(self) -> str:
        return f"pid {self.pid} [{self.matched_as}] {self.command_line}"


@dataclass(frozen=True)
class GroupStop:
    """A process group signalled as one — `record_pid` is the recorded process that named it."""

    pgid: int
    record_pid: int
    members: tuple[StopTarget, ...]

    def describe(self) -> str:
        listed = ", ".join(str(member.pid) for member in self.members)
        return f"group {self.pgid} (from pid {self.record_pid}): {listed}"


@dataclass(frozen=True)
class OwnIdentity:
    """The updater's own place in the table — everything here is protected from itself."""

    pid: int
    pgid: int | None
    ancestors: frozenset[int] = frozenset()

    @staticmethod
    def of_this_process(table: Sequence[Process]) -> "OwnIdentity":
        return OwnIdentity(
            pid=os.getpid(),
            pgid=os.getpgrp() if hasattr(os, "getpgrp") else None,
            ancestors=frozenset(ancestor_pids(table, os.getpid())),
        )


@dataclass(frozen=True)
class StopPlan:
    checkout: Path
    own: OwnIdentity
    groups: tuple[GroupStop, ...] = ()
    singles: tuple[StopTarget, ...] = ()
    records: tuple[ProcessRecord, ...] = ()
    stale: tuple[ProcessRecord, ...] = ()
    foreign: tuple[ProcessRecord, ...] = ()
    elsewhere: tuple[ProcessRecord, ...] = ()
    strays: tuple[KillTarget, ...] = ()
    shared_group_with_updater: int | None = None
    notes: tuple[str, ...] = ()

    @property
    def targets(self) -> tuple[StopTarget, ...]:
        grouped = tuple(member for group in self.groups for member in group.members)
        return grouped + self.singles

    @property
    def pids(self) -> list[int]:
        return [target.pid for target in self.targets]

    @property
    def is_empty(self) -> bool:
        return not self.groups and not self.singles

    def refuse_if_unsafe(self) -> None:
        """Raise unless every process of this install is accounted for.

        Each of these is a state in which stopping what we *can* see would leave a writer running
        while `migrate upgrade` rewrites the schema under it — so none of them is a warning.
        """
        if self.shared_group_with_updater is not None:
            raise UpdaterInsideInstall(
                f"the updater shares process group {self.shared_group_with_updater} with the "
                "install it should stop — run ./update.sh from a terminal, not from inside a "
                "backend process"
            )
        if self.foreign:
            listed = "\n".join(f"  {record.describe()}" for record in self.foreign)
            raise ForeignProcesses(
                "these processes of this install belong to another user, so they can neither be "
                f"read nor stopped:\n{listed}\n"
                "update the install as the user that runs it"
            )
        if self.strays:
            listed = "\n".join(f"  {stray.describe()}" for stray in self.strays)
            raise UnregisteredProcesses(
                "these processes look like this install but never recorded themselves (started "
                f"before the registry shipped, or not through src/app.py):\n{listed}\n"
                "stop them yourself, or let the updater stop them by pid:\n"
                "  ./update.sh --stop-unregistered"
            )

    def describe(self) -> str:
        if self.is_empty:
            lines = [f"nothing to stop in {self.checkout}"]
        else:
            lines = [f"stopping the install in {self.checkout}:"]
            lines += [f"  {group.describe()}" for group in self.groups]
            lines += [f"  {target.describe()}" for target in self.singles]
        lines += [f"  note: {note}" for note in self.notes]
        lines += [f"  stale record, will be dropped: {record.describe()}" for record in self.stale]
        lines += [f"  ignored, another checkout: {record.describe()}" for record in self.elsewhere]
        lines += [f"  another user, refusing: {record.describe()}" for record in self.foreign]
        lines += [f"  unregistered, refusing: {stray.describe()}" for stray in self.strays]
        return "\n".join(lines)


def plan_stop(
    classified: Sequence[tuple[ProcessRecord, RecordState]],
    table: Sequence[Process],
    *,
    checkout: Path,
    own: OwnIdentity,
    stop_unregistered: bool = False,
) -> StopPlan:
    """Turn records plus a process table into what will be signalled, and why."""
    verified = [record for record, state in classified if state is RecordState.VERIFIED]
    shared_group = _updater_shares_a_group_with(verified, own)

    recorded_pids = {record.pid for record in verified}
    owned_pids = set(recorded_pids)
    for pid in recorded_pids:
        owned_pids |= {
            found.pid
            for found in descendants(table, pid)
            if not _is_protected(found, own=own, recorded_pids=recorded_pids)
        }

    groups: list[GroupStop] = []
    singles: list[StopTarget] = []
    notes: list[str] = []
    covered: set[int] = set()
    for record in verified:
        verdict = _group_verdict(record, table, checkout=checkout, own=own, owned=owned_pids)
        if verdict.group is not None:
            groups.append(verdict.group)
            covered |= {member.pid for member in verdict.group.members}
            continue
        notes.append(verdict.refusal)
        for target in _one_by_one(record, table, own=own, recorded_pids=recorded_pids):
            if target.pid not in covered:
                covered.add(target.pid)
                singles.append(target)

    strays = _strays(table, checkout=checkout, own=own, covered=covered)
    if stop_unregistered:
        notes += [f"stopping an unregistered process by pid: {stray.describe()}" for stray in strays]
        singles += [_as_target(stray.process, MATCH_UNREGISTERED) for stray in strays]
        strays = []

    return StopPlan(
        checkout=checkout,
        own=own,
        groups=tuple(groups),
        singles=tuple(singles),
        records=tuple(verified),
        stale=tuple(r for r, state in classified if state is RecordState.STALE),
        foreign=tuple(r for r, state in classified if state is RecordState.FOREIGN),
        elsewhere=tuple(r for r, state in classified if state is RecordState.OTHER_CHECKOUT),
        strays=tuple(strays),
        shared_group_with_updater=shared_group,
        notes=tuple(notes),
    )


def plan_live_stop(checkout: Path | None = None, *, stop_unregistered: bool = False) -> StopPlan:
    """The same planning against the live machine. Reads only; signals nothing."""
    root = Path(checkout).resolve() if checkout is not None else project_root()
    table = read_process_table()
    return plan_stop(
        classify_records(),
        table,
        checkout=root,
        own=OwnIdentity.of_this_process(table),
        stop_unregistered=stop_unregistered,
    )


def classify_records() -> list[tuple[ProcessRecord, RecordState]]:
    """Every record with what it turned out to describe — the machine-touching half of planning."""
    return [(record, verify(record)) for record in read_records()]


def execute_stop(
    plan: StopPlan,
    *,
    report: Callable[[str], None] = lambda line: None,
    term_grace: float = TERM_GRACE_SECONDS,
    kill_grace: float = KILL_GRACE_SECONDS,
) -> list[int]:
    """Signal the plan, then prove the processes are gone.

    Nothing here trusts a return code: a signal is accepted by a process that ignores it, and a
    refused signal is not a dead process either. Liveness is what the caller needs, because a
    survivor writes to the base while `migrate upgrade` rewrites its schema, and SQLite DDL is not
    transactional across revisions. A process of another user reads as alive, never as gone.
    """
    plan.refuse_if_unsafe()
    _drop_stale_records(plan, report)
    if plan.is_empty:
        return []

    _send_to_everything(plan, TERMINATE_SIGNAL)
    _send_to_everything(plan, CONTINUE_SIGNAL)
    survivors = _wait_for_exit(plan.targets, term_grace)

    latecomers = _group_latecomers(plan)
    if latecomers:
        joined = ", ".join(str(target.pid) for target in latecomers)
        report(f"joined a group after the signal: {joined}")
        for target in latecomers:
            _signal_pid(target, TERMINATE_SIGNAL)
            _signal_pid(target, CONTINUE_SIGNAL)
        survivors += _wait_for_exit(latecomers, term_grace)

    for target in survivors:
        _signal_pid(target, FORCE_SIGNAL)
    stubborn = _wait_for_exit(survivors, kill_grace)
    if stubborn:
        raise ProcessesSurvived(_survivor_message(stubborn))

    for record in plan.records:
        withdraw(record.pid)
    stopped = plan.pids + [target.pid for target in latecomers]
    report(_stopped_summary(plan, latecomers))
    return stopped


@dataclass(frozen=True)
class _GroupVerdict:
    """Either the group to signal, or the reason it may not be signalled — never neither."""

    group: GroupStop | None = None
    refusal: str = ""


def _group_verdict(
    record: ProcessRecord,
    table: Sequence[Process],
    *,
    checkout: Path,
    own: OwnIdentity,
    owned: set[int],
) -> _GroupVerdict:
    """Whether the record's group may be signalled as one, and why not when it may not.

    Ours means: a recorded process, a descendant of one, or a link in the chain from the record up
    to the group leader — `uv run python src/app.py` makes `uv` that leader, and the README starts
    the install exactly that way.
    """
    if record.pgid is None:
        return _GroupVerdict(refusal=f"pid {record.pid} has no process group — stopping by pid")
    if own.pgid is not None and record.pgid == own.pgid:
        return _GroupVerdict(
            refusal=f"group {record.pgid} is the updater's own — stopping pid {record.pid} by pid"
        )

    chain = _chain_to_leader(record, table, checkout=checkout, own=own)
    members = _group_members(table, record.pgid)
    if not members:
        return _GroupVerdict(
            refusal=(
                f"the table shows no member of group {record.pgid} — stopping pid "
                f"{record.pid} by pid"
            )
        )
    unexplained = [member for member in members if member.pid not in owned | chain]
    if unexplained:
        listed = ", ".join(f"{member.pid} ({member.command_line})" for member in unexplained)
        return _GroupVerdict(
            refusal=f"group {record.pgid} also holds {listed} — stopping pid {record.pid} by pid"
        )
    return _GroupVerdict(
        group=GroupStop(
            pgid=record.pgid,
            record_pid=record.pid,
            members=tuple(
                _as_target(
                    member, MATCH_RECORDED if member.pid == record.pid else MATCH_GROUP_MEMBER
                )
                for member in members
            ),
        )
    )


def _updater_shares_a_group_with(
    verified: Sequence[ProcessRecord], own: OwnIdentity
) -> int | None:
    """The group the updater would be signalling itself through, if it is in one of them."""
    for record in verified:
        if own.pgid is not None and record.pgid == own.pgid:
            return record.pgid
        if record.pid == own.pid:
            return record.pgid if record.pgid is not None else own.pgid
    return None


def _chain_to_leader(
    record: ProcessRecord,
    table: Sequence[Process],
    *,
    checkout: Path,
    own: OwnIdentity,
) -> set[int]:
    """The ancestors between the record and its group leader that are ours.

    The walk stops at the first one that is not — a launcher script from outside the checkout, or
    the shell that started the updater. Whatever it stopped at stays an unexplained member of the
    group, which is what denies the group and names it to the operator.
    """
    by_pid = {process.pid: process for process in table}
    chain: set[int] = set()
    walker = by_pid.get(record.pid)
    while walker is not None and walker.pid != record.pgid:
        parent = by_pid.get(walker.ppid)
        started_the_install = (
            parent is not None
            and parent.pgid == record.pgid
            and parent.cwd == checkout
            and not _is_protected(parent, own=own, recorded_pids=set())
        )
        if not started_the_install:
            return chain
        chain.add(parent.pid)  # type: ignore[union-attr] — checked above
        walker = parent
    return chain


def _one_by_one(
    record: ProcessRecord,
    table: Sequence[Process],
    *,
    own: OwnIdentity,
    recorded_pids: set[int],
) -> list[StopTarget]:
    """The record and its descendants, deepest first — a parent that dies first orphans the rest."""
    targets = [
        _as_target(process, MATCH_DESCENDANT_OF_RECORD)
        for process in reversed(descendants(table, record.pid))
        if not _is_protected(process, own=own, recorded_pids=recorded_pids)
    ]
    if record.pid == own.pid:
        return targets
    row = next((process for process in table if process.pid == record.pid), None)
    return [
        *targets,
        _as_target(row, MATCH_RECORDED) if row is not None else _record_as_target(record),
    ]


def _record_as_target(record: ProcessRecord) -> StopTarget:
    """A recorded process the table does not show — on macOS that is another user's, and it is
    exactly the case that must be signalled from the record rather than skipped."""
    return StopTarget(
        pid=record.pid,
        start_time=record.start_time,
        command_line=record.command_line,
        matched_as=MATCH_RECORDED,
    )


def _strays(
    table: Sequence[Process], *, checkout: Path, own: OwnIdentity, covered: set[int]
) -> list[KillTarget]:
    """What the old evidence-based sweep still finds that no record explains.

    Its key is `cwd` plus an argv token — the one the research showed to be unreliable across
    operating systems and rewritable by the process itself. So a find is never signalled on that
    basis: it is reported, and the operator decides.
    """
    swept = select_kill_targets(
        table,
        checkout=checkout,
        own_pid=own.pid,
        own_process_group=own.pgid if own.pgid is not None else -1,
        own_ancestors=own.ancestors,
    )
    return [found for found in swept if found.process.pid not in covered]


def _group_members(table: Sequence[Process], pgid: int | None) -> list[Process]:
    return [process for process in table if pgid is not None and process.pgid == pgid]


def _is_protected(process: Process, *, own: OwnIdentity, recorded_pids: set[int]) -> bool:
    """A recorded ancestor is a legitimate target — that is the About button's own backend.

    Everything else above the updater stays protected: under `uv run` the updater sits in a new
    process group, so the chain up to the invoking shell is excluded by pid, not by group.
    """
    return (
        process.pid == own.pid
        or (own.pgid is not None and process.pgid == own.pgid)
        or (process.pid in own.ancestors and process.pid not in recorded_pids)
        or argv_is_vetoed(process.argv)
    )


def _as_target(process: Process, matched_as: str) -> StopTarget:
    return StopTarget(
        pid=process.pid,
        start_time=process.start_time,
        command_line=process.command_line,
        matched_as=matched_as,
    )


def _send_to_everything(plan: StopPlan, sent: signal.Signals | None) -> None:
    if sent is None:
        return
    for group in plan.groups:
        _signal_group(group.pgid, sent)
    for target in plan.singles:
        _signal_pid(target, sent)


def _group_latecomers(plan: StopPlan) -> list[StopTarget]:
    """Members that joined a signalled group between the table read and the signal.

    This is the race a ppid snapshot cannot close and a group can: the table is read again, and
    anything that appeared in a group already being stopped is stopped with it.
    """
    if not plan.groups:
        return []
    known = set(plan.pids)
    signalled_groups = {group.pgid for group in plan.groups}
    return [
        _as_target(process, MATCH_GROUP_MEMBER)
        for process in read_process_table()
        if process.pgid in signalled_groups
        and process.pid not in known
        and not _is_protected(process, own=plan.own, recorded_pids=set())
    ]


def _wait_for_exit(targets: Sequence[StopTarget], timeout: float) -> list[StopTarget]:
    """The targets still running when the timeout expires."""
    deadline = time.monotonic() + timeout
    alive = [target for target in targets if _still_running(target)]
    while alive and time.monotonic() < deadline:
        time.sleep(LIVENESS_POLL_SECONDS)
        alive = [target for target in alive if _still_running(target)]
    return alive


def _still_running(target: StopTarget) -> bool:
    return _liveness_of(target) is not Liveness.GONE


def _liveness_of(target: StopTarget) -> Liveness:
    start_time = target.start_time or None
    return process_liveness(target.pid, start_time=start_time)


def _signal_group(pgid: int, sent: signal.Signals) -> None:
    try:
        os.killpg(pgid, sent)
    except (ProcessLookupError, OSError):
        return


def _signal_pid(target: StopTarget, sent: signal.Signals | None) -> None:
    """Nothing is signalled until the pid is confirmed to still be the process that was planned:
    `psutil.Process` re-reads the number, and a number is reused."""
    if sent is None or not _is_still_the_planned_process(target):
        return
    try:
        psutil.Process(target.pid).send_signal(sent)
    except (psutil.Error, OSError):
        return


def _is_still_the_planned_process(target: StopTarget) -> bool:
    if not target.start_time:
        return True
    started = process_start_time(target.pid)
    return started is not None and abs(started - target.start_time) <= START_TIME_TOLERANCE_SECONDS


def _drop_stale_records(plan: StopPlan, report: Callable[[str], None]) -> None:
    for record in plan.stale:
        withdraw(record.pid)
        report(f"dropped a stale record: {record.describe()}")


def _survivor_message(stubborn: Iterable[StopTarget]) -> str:
    lines = []
    for target in stubborn:
        foreign = _liveness_of(target) is Liveness.FOREIGN
        belongs = " — belongs to another user" if foreign else ""
        lines.append(f"  pid {target.pid} {target.command_line}{belongs}")
    return (
        "still alive after TERM and KILL:\n"
        + "\n".join(lines)
        + "\nthe database stays untouched while anything can still write to it"
    )


def _stopped_summary(plan: StopPlan, latecomers: Sequence[StopTarget]) -> str:
    groups = ", ".join(str(group.pgid) for group in plan.groups) or "none"
    pids = ", ".join(str(target.pid) for target in plan.singles) or "none"
    raced = f", latecomers {len(latecomers)}" if latecomers else ""
    return f"stopped: groups {groups}; pids {pids}{raced}"


__all__ = [
    "CONTINUE_SIGNAL",
    "KILL_GRACE_SECONDS",
    "MATCH_DESCENDANT_OF_RECORD",
    "MATCH_GROUP_MEMBER",
    "MATCH_RECORDED",
    "MATCH_UNREGISTERED",
    "TERM_GRACE_SECONDS",
    "ForeignProcesses",
    "GroupStop",
    "OwnIdentity",
    "ProcessesSurvived",
    "StopPlan",
    "StopTarget",
    "UnregisteredProcesses",
    "UpdaterInsideInstall",
    "classify_records",
    "execute_stop",
    "plan_live_stop",
    "plan_stop",
]
