"""`app.py update`: fast-forward this checkout to `origin/<UPDATE_BRANCH>`, sync dependencies,
back the database up, migrate it and start the install back up.

`run_update` walks the steps and returns the process exit code (`EXIT_*`); everything it does to
the world goes through `UpdateHost`, which `DryRunHost` replaces with a narration. The step
order, the failure policy behind each exit code and the reasons for the invariants kept here:
`AGENTS/docs/platform/update.md`.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import traceback
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from src.core import backup, maintenance
from src.core.app_path import AppPath, project_root
from src.core.backend_launch import (
    UV_RUN_PYTHON,
    backend_command,
    base_url,
    preload_health_client,
    spawn_backend,
    wait_until_ready,
)
from src.core.config import Config
from src.core.loggers import get_logger
from src.core.maintenance import MaintenanceHeld
from src.core.update.errors import UpdateRefused
from src.core.update.stop import (
    ForeignProcesses,
    ProcessesSurvived,
    UnregisteredProcesses,
    UpdaterInsideInstall,
    execute_stop,
    plan_live_stop,
)

EXIT_OK = 0
EXIT_PRECONDITIONS = 1
EXIT_HELD = 2
EXIT_ROLLED_BACK = 3
EXIT_MIGRATION_FAILED = 4
EXIT_BACKUP_FAILED = 5
EXIT_ROLLBACK_FAILED = 6
EXIT_STOP_FAILED = 7
EXIT_BACKEND_DEAD = 8
EXIT_CRASHED = 9
EXIT_UNREGISTERED = 10
EXIT_UNSUPPORTED_PLATFORM = 11

# Windows needs a different machine, not a different signal: a job object instead of a process
# group, a launcher that does not rely on `exec`, and an answer to `uv sync` being unable to
# replace an image the running updater has mapped. Until that exists, the command says so.
WINDOWS_PLATFORM = "win32"

# Deliberately NOT configurable: `.env` is written unescaped and behind no auth, so an ENV-supplied
# remote would put `--upload-pack=…` — arbitrary code execution — one field edit away. Git already
# knows where it came from.
REMOTE = "origin"

BRANCH_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")

FETCH_COMMAND = ("git", "fetch", "--prune", REMOTE)
SYNC_COMMAND = ("uv", "sync", "--all-groups")
# Shipped code, not `AGENTS/tools/…`: `AGENTS/` is not in git, so a tool that lives only in a
# developer's checkout is missing on exactly the install this command exists for — and it would
# be missing at step 7, with the merge already done and the old schema still in place.
BACKUP_COMMAND = (*UV_RUN_PYTHON, "src/app.py", "backup")
MIGRATE_COMMAND = (*UV_RUN_PYTHON, "src/app.py", "migrate", "upgrade")

# `git ls-remote --exit-code` answers 2 when the remote has no ref matching the pattern.
LS_REMOTE_NO_MATCH = 2

# Installs reach their origin over HTTPS (stable) or SSH (a developer checkout); on either
# transport a credential prompt would block forever with the install already stopped and flagged.
# So: no terminal prompt, an askpass that answers nothing (GUI dialogs included), no interactive
# ssh. A missing credential then fails the command, which the sequence rolls back from.
GIT_NONINTERACTIVE = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_ASKPASS": "true",
    "GIT_SSH_COMMAND": "ssh -o BatchMode=yes",
}

INSPECT_TIMEOUT_SECONDS = 60
STEP_TIMEOUT_SECONDS = 600
FETCH_TIMEOUT_SECONDS = 300
# A cold `uv sync` on a slow link builds wheels and downloads an interpreter; the generic step
# budget would abort it halfway and send a working update down the rollback path.
SYNC_TIMEOUT_SECONDS = 3600
BACKUP_TIMEOUT_SECONDS = 3600
MIGRATE_TIMEOUT_SECONDS = 1800

DIRTY_ENTRIES_SHOWN = 10

RESWEEP_SECONDS = 3.0
RESWEEP_POLL_SECONDS = 0.5

BACKEND_LOG_NAME = "update_backend.log"
UPDATE_LOG_CHANNEL = "update"
DRY_RUN_MARK = "[dry-run]"


class BackendDidNotStart(UpdateRefused):
    """The install was restarted and never answered its health endpoint."""


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    def describe_failure(self) -> str:
        output = self.stderr.strip() or self.stdout.strip()
        return f"`{' '.join(self.argv)}` exited {self.returncode}\n{output}"


@dataclass(frozen=True)
class StartingPoint:
    """Where the checkout stood before anything was touched — the rollback target."""

    branch: str
    head: str


class UpdateHost:
    """Everything the sequence does to the world, in one seam.

    `inspect` asks a question and is always executed; `execute` changes the install and is what a
    dry run replaces. Keeping the two apart is what lets `DryRunHost` walk the real checkout and
    still touch nothing.
    """

    def __init__(
        self,
        checkout: Path,
        *,
        config: Config,
        report: Callable[[str], None] = print,
        stop_unregistered: bool = False,
    ) -> None:
        self.checkout = checkout
        self.config = config
        self.stop_unregistered = stop_unregistered
        self._report = report
        self._modules_before_sync: frozenset[str] | None = None

    def report(self, line: str) -> None:
        self._report(line)

    def backup_target(self) -> Path:
        """Where the copy of the database goes — chosen here and handed to the tool.

        The updater picks the path instead of reading it back out of the tool's output: a path
        recovered by parsing a report is a path that changes when a label does.
        """
        try:
            return backup.default_target(self.config)
        except backup.BackupRefused as refusal:
            raise UpdateRefused(f"nowhere to put the database copy: {refusal}") from refusal

    def inspect(
        self,
        argv: Sequence[str],
        *,
        environment_overrides: dict[str, str] | None = None,
        timeout: float = INSPECT_TIMEOUT_SECONDS,
    ) -> CommandResult:
        return self._run(argv, environment_overrides=environment_overrides, timeout=timeout)

    def execute(
        self,
        argv: Sequence[str],
        *,
        environment_overrides: dict[str, str] | None = None,
        timeout: float = STEP_TIMEOUT_SECONDS,
    ) -> CommandResult:
        self.report(f"$ {' '.join(argv)}")
        return self._run(argv, environment_overrides=environment_overrides, timeout=timeout)

    def stop_processes(self) -> None:
        plan = self._plan_stop()
        self.report(plan.describe())
        execute_stop(plan, report=self.report)
        self._stop_latecomers()

    def preload_probe_imports(self) -> None:
        preload_health_client()

    def freeze_imports(self) -> None:
        self._modules_before_sync = frozenset(sys.modules)

    def report_late_imports(self) -> None:
        """`uv sync` replaces the venv under the updater, so anything imported after it is loaded
        from the new tree into the old process — a mix that must stay impossible, not be debugged
        after the fact. Every step past the sync runs in a fresh `uv run` child for that reason."""
        if self._modules_before_sync is None:
            return
        late = sorted(set(sys.modules) - self._modules_before_sync)
        if late:
            self.report(f"WARNING: imported after `uv sync`: {', '.join(late)}")

    def start_backend(self) -> None:
        """Start the install back up in ITS role — and wait until it says it is serving.

        The role is the install's own (`WORKER_ENABLED`), not the shim's preference: an update
        that quietly drops the scheduler is an update that breaks the install it just fixed.
        """
        log_path = self._backend_log_path()
        command = spawn_backend(
            UV_RUN_PYTHON, with_worker=self.config.worker_enabled, log_path=log_path
        )
        self.report(f"started {' '.join(command)} → {log_path}")
        self._wait_until_serving(log_path)

    def raise_flag(self, reason: str) -> None:
        flag = maintenance.begin(reason)
        self.report(f"maintenance flag up ({flag.describe()})")

    def lower_flag(self) -> None:
        maintenance.end()
        self.report("maintenance flag down")

    def _plan_stop(self):
        return plan_live_stop(self.checkout, stop_unregistered=self.stop_unregistered)

    def _stop_latecomers(self) -> None:
        """The flag is up by now, so nothing *should* start — but the shim spawns a backend on
        demand, and a client that won the race would be writing to the base during the migration."""
        deadline = time.monotonic() + RESWEEP_SECONDS
        while time.monotonic() < deadline:
            time.sleep(RESWEEP_POLL_SECONDS)
            latecomers = self._plan_stop()
            if not latecomers.is_empty:
                self.report(f"raced the stop — {latecomers.describe()}")
                execute_stop(latecomers, report=self.report)

    def _wait_until_serving(self, log_path: Path) -> None:
        """A restart nobody checked is how «update complete» gets printed over a dead install."""
        address = base_url(self.config)
        # `MCP_STDIO_BOOT_TIMEOUT` is the install's only «how long a backend may take to answer»,
        # and a backend is a backend whoever started it.
        timeout = self.config.mcp_stdio_boot_timeout
        health = wait_until_ready(self.config, timeout=timeout)
        if health is None:
            raise BackendDidNotStart(
                f"{address} did not answer within {timeout}s — see {log_path}"
            )
        if not health.is_ready:
            raise BackendDidNotStart(
                f"{address} is up but not serving — {health.describe()}; see {log_path}"
            )
        self.report(f"backend is serving at {address}")

    def _backend_log_path(self) -> Path:
        return AppPath.from_root().logs / BACKEND_LOG_NAME

    def _run(
        self,
        argv: Sequence[str],
        *,
        environment_overrides: dict[str, str] | None,
        timeout: float,
    ) -> CommandResult:
        environment = {**os.environ, **(environment_overrides or {})}
        try:
            completed = subprocess.run(
                list(argv),
                cwd=str(self.checkout),
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError) as failure:
            return CommandResult(tuple(argv), returncode=-1, stderr=str(failure))
        return CommandResult(
            tuple(argv), completed.returncode, completed.stdout or "", completed.stderr or ""
        )


class DryRunHost(UpdateHost):
    """The same walk with the world untouched: questions are asked, changes are only named.

    Every line is marked, including the ones the sequence itself reports — otherwise a narrated
    «checkout is now at …» reads like something that happened.
    """

    def report(self, line: str) -> None:
        super().report(f"{DRY_RUN_MARK} {line}")

    def execute(
        self,
        argv: Sequence[str],
        *,
        environment_overrides: dict[str, str] | None = None,
        timeout: float = STEP_TIMEOUT_SECONDS,
    ) -> CommandResult:
        self.report(f"would run: {' '.join(argv)}")
        return CommandResult(tuple(argv), returncode=0)

    def stop_processes(self) -> None:
        self.report(self._plan_stop().describe())

    def start_backend(self) -> None:
        command = backend_command(UV_RUN_PYTHON, with_worker=self.config.worker_enabled)
        self.report(f"would start: {' '.join(command)}")

    def freeze_imports(self) -> None:
        self.report("would watch for modules imported after the sync")

    def report_late_imports(self) -> None:
        return None

    def raise_flag(self, reason: str) -> None:
        self.report(f"would raise the maintenance flag ({maintenance.flag_path()}): {reason}")

    def lower_flag(self) -> None:
        self.report("would lower the maintenance flag")


def validate_branch(branch: str) -> str:
    """The branch name, or a refusal.

    ENV is hostile input here — the settings page writes `.env` unescaped and behind no auth — so
    the value must never be able to turn into a git *option* or to escape `refs/remotes/origin/`:
    it has to start with an alphanumeric, may not traverse with `..`, and may not name a ref lock.
    """
    unusable = (
        not BRANCH_PATTERN.fullmatch(branch)
        or ".." in branch
        or branch.endswith(".lock")
    )
    if unusable:
        raise UpdateRefused(f"UPDATE_BRANCH={branch!r} is not a usable branch name")
    return branch


def run_update(host: UpdateHost, *, branch: str) -> int:
    """Walk the sequence, turning even an unforeseen failure into an exit code and a report.

    A traceback escaping this call is the worst outcome available: the operator is left with a
    stack trace instead of the state of their install, and every step after the one that broke —
    including the restart — is skipped silently. So anything the walk did not expect ends as
    `EXIT_CRASHED` with the recovery commands, the way every foreseen failure does. The flag is
    left as the walk left it: a flag whose updater has died is already inactive (liveness is the
    pid, not the clock), while a crash after the migration is exactly when nothing may start.
    """
    try:
        return _walk_the_sequence(host, branch)
    except Exception:  # noqa: BLE001 — the exit code IS the error handling here
        host.report(f"the update crashed:\n{traceback.format_exc()}")
        host.report(_crash_recovery())
        return EXIT_CRASHED
    finally:
        host.report_late_imports()


def _walk_the_sequence(host: UpdateHost, branch: str) -> int:
    """The steps themselves; the return value is the process exit code.

    Two orderings are load-bearing and must not be tidied away:

    - the flag goes up BEFORE anything is killed — the MCP shim respawns the backend on demand,
      so killing first is a race a client can win;
    - the flag comes down BEFORE the restart — a backend started under an active flag hits the
      gate in `main()` and exits 1, which would end the update "successfully" with nothing running.

    A failed migration is the one outcome that keeps the flag up: the code is already new, and
    letting anything start over a stale schema is exactly what this command exists to prevent.
    """
    if sys.platform == WINDOWS_PLATFORM:
        host.report(_windows_refusal())
        return EXIT_UNSUPPORTED_PLATFORM

    try:
        start = _verify_preconditions(host, branch)
    except UpdateRefused as refusal:
        host.report(f"refusing to update: {refusal}")
        return EXIT_PRECONDITIONS
    host.report(f"preconditions ok: clean tree on {start.branch} at {start.head}")

    try:
        host.raise_flag(f"update {start.branch} to {REMOTE}/{start.branch}")
    except MaintenanceHeld as held:
        host.report(f"refusing to update: {held}")
        return EXIT_HELD

    try:
        target = _stop_and_fast_forward(host, start)
    except UnregisteredProcesses as refusal:
        host.report(f"refusing to update: {refusal}")
        host.lower_flag()
        return EXIT_UNREGISTERED
    except (ProcessesSurvived, ForeignProcesses, UpdaterInsideInstall) as refusal:
        host.report(f"refusing to update: {refusal}")
        host.lower_flag()
        host.report(_survivor_recovery())
        return EXIT_STOP_FAILED
    except UpdateRefused as failure:
        host.report(f"failed before the database was touched: {failure}")
        try:
            _roll_back(host, start)
        except UpdateRefused as broken_rollback:
            host.report(f"the rollback itself failed: {broken_rollback}")
            host.report(_rollback_recovery(start))
            return EXIT_ROLLBACK_FAILED
        host.lower_flag()
        return _restart(host, outcome=EXIT_ROLLED_BACK)
    host.report(f"checkout is now at {target}")

    try:
        copy_path = _back_up_database(host)
    except UpdateRefused as failure:
        host.report(f"backup failed, so nothing will be migrated: {failure}")
        host.lower_flag()
        return _restart(host, outcome=EXIT_BACKUP_FAILED)
    host.report(f"database backed up to {copy_path}")

    try:
        _apply_migrations(host)
    except UpdateRefused as failure:
        host.report(f"migration failed: {failure}")
        host.report(_migration_recovery(copy_path))
        return EXIT_MIGRATION_FAILED

    host.lower_flag()
    outcome = _restart(host, outcome=EXIT_OK)
    if outcome == EXIT_OK:
        host.report("update complete")
    return outcome


def _restart(host: UpdateHost, *, outcome: int) -> int:
    """Bring the install back up; a backend that never answers outranks any other outcome."""
    try:
        host.start_backend()
    except BackendDidNotStart as failure:
        host.report(f"the install is DOWN after the restart: {failure}")
        return EXIT_BACKEND_DEAD
    return outcome


def update_command(*, dry_run: bool = False, stop_unregistered: bool = False) -> int:
    """`app.py update` — the branch comes from ENV, the checkout is the one this file lives in."""
    config = Config()
    build_host = DryRunHost if dry_run else UpdateHost
    host = build_host(
        project_root(),
        config=config,
        report=_reporter(dry_run=dry_run),
        stop_unregistered=stop_unregistered,
    )
    return run_update(host, branch=config.update_branch)


def _reporter(*, dry_run: bool) -> Callable[[str], None]:
    """A real run is recorded — a failure must stay diagnosable after the terminal is closed."""
    if dry_run:
        return print
    log = get_logger(UPDATE_LOG_CHANNEL)
    return lambda line: log.info("%s", line)


def _verify_preconditions(host: UpdateHost, branch: str) -> StartingPoint:
    """Refuse everything that makes a fast-forward unsafe — before the flag, before the kill."""
    validate_branch(branch)

    toplevel = _must_succeed(host.inspect(["git", "rev-parse", "--show-toplevel"])).stdout.strip()
    if Path(toplevel).resolve() != host.checkout:
        raise UpdateRefused(f"{host.checkout} is not a git checkout root (git says {toplevel!r})")

    listed = _must_succeed(host.inspect(["git", "status", "--porcelain"])).stdout.splitlines()
    dirty = [entry for entry in listed if entry.strip()]
    if dirty:
        raise UpdateRefused(
            "the working tree is not clean — commit or clean it first:\n"
            + _first_lines(dirty, DIRTY_ENTRIES_SHOWN)
        )

    checked_out_branch = _must_succeed(
        host.inspect(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    ).stdout.strip()
    if checked_out_branch != branch:
        raise UpdateRefused(
            f"checkout is on {checked_out_branch!r} but UPDATE_BRANCH is {branch!r} — an update "
            "fast-forwards a branch, it does not move the install to another line of code"
        )

    _verify_remote_has_branch(host, branch)
    head = _must_succeed(host.inspect(["git", "rev-parse", "HEAD"])).stdout.strip()
    return StartingPoint(branch=branch, head=head)


def _stop_and_fast_forward(host: UpdateHost, start: StartingPoint) -> str:
    """Stop the install, then bring code and dependencies to the head of the remote branch."""
    host.stop_processes()
    _must_succeed(
        host.execute(
            FETCH_COMMAND,
            environment_overrides=GIT_NONINTERACTIVE,
            timeout=FETCH_TIMEOUT_SECONDS,
        )
    )
    target = _resolve_fetched_commit(host, start.branch)
    _must_succeed(host.execute(["git", "merge", "--ff-only", target]))
    host.preload_probe_imports()
    host.freeze_imports()
    _must_succeed(host.execute(SYNC_COMMAND, timeout=SYNC_TIMEOUT_SECONDS))
    return target


def _back_up_database(host: UpdateHost) -> str:
    """A copy is mandatory: on SQLite each revision commits on its own, so a failed chain leaves
    a half-migrated base that no rollback can undo."""
    copy_path = host.backup_target()
    _must_succeed(
        host.execute((*BACKUP_COMMAND, str(copy_path)), timeout=BACKUP_TIMEOUT_SECONDS)
    )
    return str(copy_path)


def _apply_migrations(host: UpdateHost) -> None:
    _must_succeed(host.execute(MIGRATE_COMMAND, timeout=MIGRATE_TIMEOUT_SECONDS))


def _roll_back(host: UpdateHost, start: StartingPoint) -> None:
    """Safe only because the merge was strictly fast-forward onto a tree verified clean.

    A rollback that fails is not a lesser outcome to report and move on from: lowering the flag
    and starting a backend over a half-written venv would end the command with a tidy exit 3
    over an install that cannot run at all.
    """
    host.report(f"rolling the checkout back to {start.head}")
    reset = host.execute(["git", "reset", "--hard", start.head])
    if not reset.succeeded:
        raise UpdateRefused(f"the checkout is NOT back at {start.head}: {reset.describe_failure()}")
    restored = host.execute(SYNC_COMMAND, timeout=SYNC_TIMEOUT_SECONDS)
    if not restored.succeeded:
        raise UpdateRefused(f"dependencies not restored: {restored.describe_failure()}")


def _verify_remote_has_branch(host: UpdateHost, branch: str) -> None:
    """Asked of the remote itself, before anything is stopped.

    The local `refs/remotes/origin/<branch>` is only as fresh as the last fetch, so a branch
    created after the clone would be reported missing by a local lookup; and a fetch that would
    hang on credentials hangs here, with the install still running and unflagged.
    """
    probe = host.inspect(
        ["git", "ls-remote", "--exit-code", "--heads", REMOTE, f"refs/heads/{branch}"],
        environment_overrides=GIT_NONINTERACTIVE,
    )
    if probe.returncode == LS_REMOTE_NO_MATCH:
        raise UpdateRefused(f"{REMOTE} has no branch {branch!r}")
    if not probe.succeeded:
        raise UpdateRefused(f"could not ask {REMOTE} for {branch!r}: {probe.describe_failure()}")


def _resolve_fetched_commit(host: UpdateHost, branch: str) -> str:
    """The just-fetched branch as a commit id — the only form the merge ever sees."""
    ref = f"refs/remotes/{REMOTE}/{branch}^{{commit}}"
    resolved = host.inspect(["git", "rev-parse", "--verify", ref])
    if not resolved.succeeded:
        raise UpdateRefused(f"the fetch did not bring {ref} (is the remote's refspec narrowed?)")
    return resolved.stdout.strip()


def _first_lines(lines: Sequence[str], shown: int) -> str:
    listed = "\n".join(lines[:shown])
    hidden = len(lines) - shown
    return listed if hidden <= 0 else f"{listed}\n  … and {hidden} more"


def _must_succeed(result: CommandResult) -> CommandResult:
    if not result.succeeded:
        raise UpdateRefused(result.describe_failure())
    return result


def _migration_recovery(backup_path: str) -> str:
    return (
        "the code stays new and the maintenance flag stays UP — nothing may start on a stale "
        "schema. Recovery:\n"
        "  see what is pending:  uv run python src/app.py migrate check\n"
        "  retry the update:     ./update.sh\n"
        f"  pre-migration copy:   {backup_path}\n"
        f"  the flag itself:      {maintenance.flag_path()}"
    )


def _rollback_recovery(start: StartingPoint) -> str:
    return (
        "the maintenance flag stays UP and nothing is started — the checkout, the venv, or both "
        "are in an unknown state. Recovery:\n"
        f"  put the code back:    git reset --hard {start.head}\n"
        "  rebuild the venv:     uv sync --all-groups\n"
        "  then retry:           ./update.sh\n"
        f"  the flag itself:      {maintenance.flag_path()}"
    )


def _crash_recovery() -> str:
    return (
        "the update stopped where the traceback says and went no further — how far it got is in "
        "the lines above. Recovery:\n"
        "  what is running:      ./update.sh --dry-run\n"
        "  what is pending:      uv run python src/app.py migrate check\n"
        "  retry (every step is a no-op on an install that is already current):  ./update.sh\n"
        f"  the flag itself:      {maintenance.flag_path()}"
    )


def _survivor_recovery() -> str:
    """`pgrep -af src/app.py` is deliberately not printed here: the pattern matches the coding
    agent's own session and every shell that quotes it, and an operator who runs what a message
    tells them to run is how the agent got killed once already."""
    return (
        "nothing was fetched, merged or migrated. A process of this install would not die — "
        "find out what holds it:\n"
        "  what the plan sees:   ./update.sh --dry-run\n"
        "  what recorded itself:  ls runtime/processes/\n"
        "  then retry:           ./update.sh"
    )


def _windows_refusal() -> str:
    return (
        "refusing to update: Windows is not supported by this command — it stops the install "
        "through POSIX process groups, and `uv sync` cannot replace files this updater has "
        "mapped. Update by hand instead:\n"
        "  stop the app\n"
        "  git pull --ff-only\n"
        "  uv sync --all-groups\n"
        "  uv run python src/app.py backup\n"
        "  uv run python src/app.py migrate upgrade\n"
        "  start the app"
    )


__all__ = [
    "BRANCH_PATTERN",
    "EXIT_BACKEND_DEAD",
    "EXIT_BACKUP_FAILED",
    "EXIT_CRASHED",
    "EXIT_HELD",
    "EXIT_MIGRATION_FAILED",
    "EXIT_OK",
    "EXIT_PRECONDITIONS",
    "EXIT_ROLLBACK_FAILED",
    "EXIT_ROLLED_BACK",
    "EXIT_STOP_FAILED",
    "EXIT_UNREGISTERED",
    "EXIT_UNSUPPORTED_PLATFORM",
    "GIT_NONINTERACTIVE",
    "SYNC_TIMEOUT_SECONDS",
    "BackendDidNotStart",
    "CommandResult",
    "DryRunHost",
    "StartingPoint",
    "UpdateHost",
    "run_update",
    "update_command",
    "validate_branch",
]
