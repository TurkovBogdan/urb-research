"""The update sequence: what it refuses, what it rolls back, and what it leaves behind.

The git/subprocess layer is a scripted fake — this suite must never fetch, merge, sync, back up,
migrate, signal a process or raise the real maintenance flag. `FakeHost` overrides every method of
`UpdateHost` that touches the world, so a forgotten override would be a missing attribute, not a
real command.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from src.core import maintenance
from src.core.config import Config
from src.core.maintenance import MaintenanceHeld
from src.core.update import (
    EXIT_BACKEND_DEAD,
    EXIT_BACKUP_FAILED,
    EXIT_HELD,
    EXIT_MIGRATION_FAILED,
    EXIT_OK,
    EXIT_PRECONDITIONS,
    EXIT_ROLLBACK_FAILED,
    EXIT_ROLLED_BACK,
    EXIT_STOP_FAILED,
    SYNC_TIMEOUT_SECONDS,
    BackendDidNotStart,
    CommandResult,
    DryRunHost,
    ProcessesSurvived,
    UpdateHost,
    run_update,
    validate_branch,
)

CHECKOUT = Path("/srv/urb-research")
BRANCH = "main"
HEAD_BEFORE = "1111111111111111111111111111111111111111"
REMOTE_HEAD = "2222222222222222222222222222222222222222"
DATABASE_FILE = CHECKOUT / "runtime" / "prod" / "app.sqlite3"
BACKUP_PATH = CHECKOUT / "runtime" / "prod" / "backup" / "app.sqlite3.20260912-010203"


def install_config(**over) -> Config:
    """The install as the updater sees it — a file base and a worker, like stable runs."""
    settings = dict(db_provider="sqlite", db_path=str(DATABASE_FILE), worker_enabled=True)
    return Config(**{**settings, **over})


class FakeHost(UpdateHost):
    """A scripted checkout: answers the sequence's questions, records what it would change."""

    def __init__(
        self,
        *,
        current_branch: str = BRANCH,
        dirty: str = "",
        remote_head: str | None = REMOTE_HEAD,
        tracking_ref_before_fetch: bool = True,
        flag_held: bool = False,
        failing_commands: Sequence[str] = (),
        survivors: bool = False,
        backend_comes_up: bool = True,
    ) -> None:
        self.events: list[str] = []
        self.inspected: list[str] = []
        self.executed: list[str] = []
        self.timeouts: dict[str, float] = {}
        self.environments: dict[str, dict[str, str] | None] = {}
        self.head = HEAD_BEFORE
        self.flag_up = False
        self.backend_started = False
        self._current_branch = current_branch
        self._dirty = dirty
        self._remote_head = remote_head
        # `refs/remotes/origin/<branch>` exists locally only once a fetch has brought it — a
        # branch created after the clone is on the remote and nowhere in the checkout.
        self._tracking_ref_present = tracking_ref_before_fetch
        self._flag_held = flag_held
        # Each scripted failure fires ONCE: the rollback re-runs `uv sync`, and a failure that
        # never heals would turn every rollback test into a test about a broken rollback.
        self._pending_failures = list(failing_commands)
        self._survivors = survivors
        self._backend_comes_up = backend_comes_up
        super().__init__(CHECKOUT, config=install_config(), report=self.events.append)

    def backup_target(self) -> Path:
        return BACKUP_PATH

    def inspect(
        self,
        argv: Sequence[str],
        *,
        environment_overrides: dict[str, str] | None = None,
        timeout: float = 0.0,
    ) -> CommandResult:
        answers = {
            "git rev-parse --show-toplevel": str(CHECKOUT),
            "git status --porcelain": self._dirty,
            "git rev-parse --abbrev-ref HEAD": self._current_branch,
            "git rev-parse HEAD": self.head,
        }
        command = " ".join(argv)
        self.inspected.append(command)
        self.environments[command] = environment_overrides
        if command.startswith("git ls-remote --exit-code --heads origin refs/heads/"):
            if self._remote_head is None:
                return CommandResult(tuple(argv), returncode=2)
            listing = f"{self._remote_head}\t{argv[-1]}\n"
            return CommandResult(tuple(argv), returncode=0, stdout=listing)
        if command.startswith("git rev-parse --verify refs/remotes/origin/"):
            if self._remote_head is None or not self._tracking_ref_present:
                return CommandResult(tuple(argv), returncode=128, stderr="fatal: Needed a ref")
            return CommandResult(tuple(argv), returncode=0, stdout=self._remote_head + "\n")
        return CommandResult(tuple(argv), returncode=0, stdout=answers[command] + "\n")

    def execute(
        self,
        argv: Sequence[str],
        *,
        environment_overrides: dict[str, str] | None = None,
        timeout: float = 0.0,
    ) -> CommandResult:
        command = " ".join(argv)
        self.executed.append(command)
        self.timeouts[command] = timeout
        self.environments[command] = environment_overrides
        failure = next((f for f in self._pending_failures if f in command), None)
        if failure is not None:
            self._pending_failures.remove(failure)
            return CommandResult(tuple(argv), returncode=1, stderr="scripted failure")
        if command.startswith("git fetch "):
            self._tracking_ref_present = True
        if command.startswith("git merge --ff-only ") or command.startswith("git reset --hard "):
            self.head = argv[-1]
        return CommandResult(tuple(argv), returncode=0)

    def stop_processes(self) -> None:
        if self._survivors:
            raise ProcessesSurvived("still alive after TERM and KILL: 4242")
        self.events.append("stopped the install")

    def start_backend(self) -> None:
        self.backend_started = True
        self.events.append("started the backend")
        if not self._backend_comes_up:
            raise BackendDidNotStart("http://127.0.0.1:12200 did not answer within 30s")

    def raise_flag(self, reason: str) -> None:
        if self._flag_held:
            raise MaintenanceHeld("maintenance flag held by pid 4242 (another update)")
        self.flag_up = True
        self.events.append(f"maintenance flag up ({reason})")

    def lower_flag(self) -> None:
        self.flag_up = False
        self.events.append("maintenance flag down")


def ran(host: FakeHost, fragment: str) -> bool:
    return any(fragment in command for command in host.executed)


# ── the happy path ───────────────────────────────────────────────────────────

@pytest.mark.pure
def test_updates_in_order_and_ends_with_the_flag_down_before_the_restart():
    host = FakeHost()

    assert run_update(host, branch=BRANCH) == EXIT_OK
    assert host.executed == [
        "git fetch --prune origin",
        f"git merge --ff-only {REMOTE_HEAD}",
        "uv sync --all-groups",
        f"uv run python src/app.py backup {BACKUP_PATH}",
        "uv run python src/app.py migrate upgrade",
    ]
    assert host.head == REMOTE_HEAD
    assert host.flag_up is False
    assert host.backend_started is True
    assert host.events.index("maintenance flag down") < host.events.index("started the backend")


@pytest.mark.pure
def test_the_flag_goes_up_before_anything_is_stopped():
    host = FakeHost()

    run_update(host, branch=BRANCH)

    flag_raised = next(
        step for step, line in enumerate(host.events) if line.startswith("maintenance flag up")
    )
    assert flag_raised < host.events.index("stopped the install")


@pytest.mark.pure
def test_the_backup_runs_shipped_code_and_is_told_where_to_write():
    """`AGENTS/` is not in git, and a path scraped back out of the tool's output is a path that
    breaks when a label changes — so the command is `src/app.py backup <target>`."""
    host = FakeHost()

    run_update(host, branch=BRANCH)

    backup_run = next(command for command in host.executed if " backup " in command)
    assert backup_run == f"uv run python src/app.py backup {BACKUP_PATH}"
    assert not any("AGENTS/" in command for command in host.executed)
    assert f"database backed up to {BACKUP_PATH}" in host.events


@pytest.mark.pure
def test_the_dependency_sync_gets_its_own_generous_timeout():
    """A cold `uv sync` builds wheels and may fetch an interpreter; the generic step budget would
    abort a working update halfway and send it down the rollback path."""
    host = FakeHost()

    run_update(host, branch=BRANCH)

    assert host.timeouts["uv sync --all-groups"] == SYNC_TIMEOUT_SECONDS
    assert SYNC_TIMEOUT_SECONDS >= 3600


@pytest.mark.pure
def test_the_backup_target_lands_next_to_the_database_it_copies():
    """The path the updater hands the tool: chosen from the install's own config, timestamped,
    never an existing file."""
    host = UpdateHost(CHECKOUT, config=install_config(), report=lambda line: None)

    target = host.backup_target()

    assert target.parent == DATABASE_FILE.parent / "backup"
    assert target.name.startswith(f"{DATABASE_FILE.name}.")


# ── preconditions: nothing is touched ────────────────────────────────────────

@pytest.mark.pure
def test_refuses_a_dirty_tree_before_raising_the_flag():
    host = FakeHost(dirty=" M src/core/update.py\n?? runtime/scratch")

    assert run_update(host, branch=BRANCH) == EXIT_PRECONDITIONS
    assert host.executed == []
    assert host.flag_up is False
    assert host.backend_started is False
    assert any("working tree is not clean" in line for line in host.events)


@pytest.mark.pure
def test_refuses_a_checkout_on_another_branch():
    host = FakeHost(current_branch="dev")

    assert run_update(host, branch=BRANCH) == EXIT_PRECONDITIONS
    assert host.executed == []
    assert any("does not move the install to another line of code" in line for line in host.events)


@pytest.mark.pure
def test_refuses_a_branch_the_remote_does_not_have():
    host = FakeHost(remote_head=None)

    assert run_update(host, branch=BRANCH) == EXIT_PRECONDITIONS
    assert host.executed == []
    assert any("origin has no branch" in line for line in host.events)


@pytest.mark.pure
def test_the_branch_is_asked_of_the_remote_not_of_the_last_fetch():
    """A branch created after the clone has no `refs/remotes/origin/<b>` yet; only the remote
    itself can say it exists, and the update must not refuse it."""
    host = FakeHost(tracking_ref_before_fetch=False)

    assert run_update(host, branch=BRANCH) == EXIT_OK
    assert f"git ls-remote --exit-code --heads origin refs/heads/{BRANCH}" in host.inspected
    assert host.head == REMOTE_HEAD


@pytest.mark.pure
def test_git_is_never_allowed_to_wait_for_credentials():
    """Both transports are covered: an askpass that answers nothing (HTTPS), batch-mode ssh, and
    no terminal prompt — a prompt would block forever with the install stopped and flagged."""
    host = FakeHost()

    run_update(host, branch=BRANCH)

    probe = f"git ls-remote --exit-code --heads origin refs/heads/{BRANCH}"
    for command in (probe, "git fetch --prune origin"):
        environment = host.environments[command]
        assert environment is not None, command
        assert environment["GIT_TERMINAL_PROMPT"] == "0"
        assert environment["GIT_ASKPASS"]
        assert "BatchMode=yes" in environment["GIT_SSH_COMMAND"]


@pytest.mark.pure
def test_refuses_an_unusable_branch_name_without_asking_git():
    host = FakeHost()

    assert run_update(host, branch="--upload-pack=touch /tmp/pwned") == EXIT_PRECONDITIONS
    assert host.executed == []


@pytest.mark.pure
def test_another_updater_holding_the_flag_stops_the_run():
    host = FakeHost(flag_held=True)

    assert run_update(host, branch=BRANCH) == EXIT_HELD
    assert host.executed == []
    assert host.backend_started is False


# ── failure policy ───────────────────────────────────────────────────────────

@pytest.mark.pure
def test_failed_sync_rolls_the_tree_back_drops_the_flag_and_restarts():
    host = FakeHost(failing_commands=("uv sync",))

    assert run_update(host, branch=BRANCH) == EXIT_ROLLED_BACK
    assert host.head == HEAD_BEFORE
    assert ran(host, f"git reset --hard {HEAD_BEFORE}")
    assert host.flag_up is False
    assert host.backend_started is True
    assert not ran(host, "app.py backup")
    assert not ran(host, "migrate upgrade")


@pytest.mark.pure
def test_failed_fetch_never_reaches_the_database():
    host = FakeHost(failing_commands=("git fetch",))

    assert run_update(host, branch=BRANCH) == EXIT_ROLLED_BACK
    assert not ran(host, "app.py backup")
    assert host.flag_up is False


@pytest.mark.pure
def test_a_rollback_that_fails_keeps_the_flag_up_and_starts_nothing():
    """Exit 3 over a half-written venv is a lie the operator acts on: the flag stays up and the
    recovery commands are printed instead."""
    host = FakeHost(failing_commands=("git fetch", "git reset --hard"))

    assert run_update(host, branch=BRANCH) == EXIT_ROLLBACK_FAILED
    assert ran(host, f"git reset --hard {HEAD_BEFORE}")
    assert host.flag_up is True
    assert host.backend_started is False
    assert any("the rollback itself failed" in line for line in host.events)
    assert any(f"git reset --hard {HEAD_BEFORE}" in line for line in host.events)


@pytest.mark.pure
def test_processes_that_will_not_die_stop_the_update_before_anything_moves():
    host = FakeHost(survivors=True)

    assert run_update(host, branch=BRANCH) == EXIT_STOP_FAILED
    assert host.executed == []
    assert host.flag_up is False
    assert host.backend_started is False
    assert any("still alive after TERM and KILL" in line for line in host.events)


@pytest.mark.pure
def test_a_backend_that_never_comes_up_is_not_a_successful_update():
    host = FakeHost(backend_comes_up=False)

    assert run_update(host, branch=BRANCH) == EXIT_BACKEND_DEAD
    assert ran(host, "migrate upgrade")
    assert host.flag_up is False
    assert any("the install is DOWN after the restart" in line for line in host.events)
    assert not any(line == "update complete" for line in host.events)


@pytest.mark.pure
def test_failed_backup_refuses_before_the_schema_is_touched():
    host = FakeHost(failing_commands=("app.py backup",))

    assert run_update(host, branch=BRANCH) == EXIT_BACKUP_FAILED
    assert not ran(host, "migrate upgrade")
    assert host.head == REMOTE_HEAD
    assert host.flag_up is False
    assert host.backend_started is True


@pytest.mark.pure
def test_failed_migration_keeps_the_flag_up_and_starts_nothing():
    host = FakeHost(failing_commands=("migrate upgrade",))

    assert run_update(host, branch=BRANCH) == EXIT_MIGRATION_FAILED
    assert host.flag_up is True
    assert host.backend_started is False
    assert host.head == REMOTE_HEAD
    assert not ran(host, "git reset --hard")
    assert any(str(BACKUP_PATH) in line for line in host.events)


# ── the branch validator ─────────────────────────────────────────────────────

@pytest.mark.pure
@pytest.mark.parametrize("branch", ["main", "dev", "release/2.0", "v1.2.3-rc1", "feature/x.y"])
def test_validator_accepts_ordinary_branch_names(branch: str):
    assert validate_branch(branch) == branch


@pytest.mark.pure
@pytest.mark.parametrize(
    "branch",
    [
        "",
        "-x",
        "--upload-pack=/bin/sh",
        "--exec=rm -rf /",
        "main;rm -rf /",
        "main branch",
        "main\nUPDATE_BRANCH=evil",
        "$(whoami)",
        "../../etc/passwd",
        "feature/..",
        "main.lock",
        "refs/heads/main^{commit}",
    ],
)
def test_validator_rejects_injection_shaped_values(branch: str):
    from src.core.update import UpdateRefused

    with pytest.raises(UpdateRefused):
        validate_branch(branch)


# ── the dry run touches nothing ──────────────────────────────────────────────

@pytest.mark.pure
def test_dry_run_narrates_instead_of_running_and_leaves_no_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(maintenance, "project_root", lambda: tmp_path)
    reported: list[str] = []
    host = DryRunHost(tmp_path, config=install_config(), report=reported.append)

    result = host.execute(["git", "merge", "--ff-only", REMOTE_HEAD])
    host.raise_flag("update main to origin/main")
    host.lower_flag()
    host.start_backend()

    assert result.succeeded
    assert not maintenance.flag_path().exists()
    assert all(line.startswith("[dry-run]") for line in reported)
    assert any("would start: uv run python" in line for line in reported)
