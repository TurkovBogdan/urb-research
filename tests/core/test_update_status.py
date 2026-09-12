"""Update status: what the installation reports, and when it refuses to start an update."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from src.core.maintenance import MaintenanceFlag
from src.core.update import spawn, status
from src.core.update.errors import UpdateRefused

pytestmark = pytest.mark.pure


@pytest.fixture(autouse=True)
def forget_spawned_update(monkeypatch: pytest.MonkeyPatch):
    """`spawn` remembers the updater it started; a test must not inherit a previous one."""
    monkeypatch.setattr(spawn, "_spawned", None)


@pytest.fixture
def git_answers(monkeypatch: pytest.MonkeyPatch):
    """Replace git with a table of answers keyed by its arguments; anything absent «failed»."""
    answers: dict[tuple[str, ...], str | None] = {}

    def fake_git_text(argv):
        return answers.get(tuple(argv))

    monkeypatch.setattr(status, "_git_text", fake_git_text)
    return answers


@pytest.fixture
def quiet_fetch(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(status, "_fetch", lambda: None)


def test_installation_reports_manifest_and_build(git_answers):
    git_answers[("rev-parse", "--abbrev-ref", "HEAD")] = "main"
    git_answers[("rev-parse", "--short", "HEAD")] = "abc1234"
    git_answers[("describe", "--tags", "--long", "--dirty")] = "v1.0.0-5-gabc1234"
    git_answers[("status", "--porcelain")] = ""

    reported = status.installation(followed_branch="main")

    assert reported.version == status.installed_release().version
    assert reported.commit == "abc1234"
    assert reported.describes_as == "v1.0.0-5-gabc1234"
    assert reported.dirty is False
    assert reported.branch_matches is True


def test_installation_flags_a_dirty_tree(git_answers):
    git_answers[("rev-parse", "--abbrev-ref", "HEAD")] = "main"
    git_answers[("status", "--porcelain")] = " M src/app.py"

    assert status.installation(followed_branch="main").dirty is True


def test_installation_flags_a_checkout_on_another_branch(git_answers):
    """The update command refuses this case, so the page has to show it rather than hide it."""
    git_answers[("rev-parse", "--abbrev-ref", "HEAD")] = "dev"
    git_answers[("status", "--porcelain")] = ""

    reported = status.installation(followed_branch="main")

    assert reported.checked_out_branch == "dev"
    assert reported.branch_matches is False


def test_installation_without_git_knows_nothing_rather_than_claiming_clean(git_answers):
    """`dirty=False` here would be a claim made out of ignorance — and it unlocks the button."""
    reported = status.installation(followed_branch="main")

    assert reported.commit is None
    assert reported.checked_out_branch is None
    assert reported.dirty is None


def test_upstream_reads_the_head_of_the_followed_branch(quiet_fetch, git_answers):
    git_answers[("rev-parse", "--short", "origin/main")] = "def5678"
    git_answers[("show", "origin/main:pyproject.toml")] = '[project]\nversion = "1.4.0"\n'
    git_answers[("rev-list", "--left-right", "--count", "HEAD...origin/main")] = "0\t7"

    offered = status.upstream(followed_branch="main")

    assert offered.version == "1.4.0"
    assert offered.commit == "def5678"
    assert offered.behind == 7
    assert offered.ahead == 0


def test_upstream_counts_local_commits_the_remote_has_never_seen(quiet_fetch, git_answers):
    """Ahead is what turns a fast-forward into a refusal, so it is reported next to behind."""
    git_answers[("rev-parse", "--short", "origin/main")] = "def5678"
    git_answers[("rev-list", "--left-right", "--count", "HEAD...origin/main")] = "3\t0"

    offered = status.upstream(followed_branch="main")

    assert offered.ahead == 3
    assert offered.behind == 0


def test_upstream_distance_is_unknown_when_git_refuses(quiet_fetch, git_answers):
    git_answers[("rev-parse", "--short", "origin/main")] = "def5678"

    offered = status.upstream(followed_branch="main")

    assert offered.behind is None
    assert offered.ahead is None


def test_upstream_has_no_version_when_the_branch_predates_the_manifest(quiet_fetch, git_answers):
    git_answers[("rev-parse", "--short", "origin/main")] = "def5678"

    assert status.upstream(followed_branch="main").version is None


def test_upstream_separates_a_missing_branch_from_an_outage(quiet_fetch, git_answers):
    with pytest.raises(status.UpstreamBranchMissing):
        status.upstream(followed_branch="main")


def test_upstream_refuses_when_the_fetch_fails(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        status,
        "_git",
        lambda argv, timeout=None: subprocess.CompletedProcess(argv, 128, "", "no route to host"),
    )

    with pytest.raises(status.UpstreamUnreachable, match="no route to host"):
        status.upstream(followed_branch="main")


def test_upstream_refuses_an_unusable_branch_name(monkeypatch: pytest.MonkeyPatch):
    """The name goes into git arguments, so it passes the command's own validator first."""
    spied: list[list[str]] = []
    monkeypatch.setattr(status, "_git", lambda argv, timeout=None: spied.append(list(argv)))

    with pytest.raises(UpdateRefused):
        status.upstream(followed_branch="../evil")

    assert spied == []


def test_spawn_refuses_while_another_updater_holds_the_flag(monkeypatch: pytest.MonkeyPatch):
    held = MaintenanceFlag(pid=4242, started_at=datetime(2026, 9, 12, 10, 0, 0), reason="update")
    monkeypatch.setattr(spawn.maintenance, "active", lambda: held)

    with pytest.raises(spawn.UpdateAlreadyRunning) as refusal:
        spawn.spawn_update()

    assert "4242" in str(refusal.value)


def test_spawn_refuses_a_checkout_the_sequence_would_reject(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(spawn.maintenance, "active", lambda: None)

    with pytest.raises(spawn.CheckoutNotUpdatable, match="not clean"):
        spawn.spawn_update(refusal="the working tree is not clean")


def test_spawn_refuses_a_checkout_without_the_script(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(spawn.maintenance, "active", lambda: None)
    monkeypatch.setattr(spawn, "project_root", lambda: tmp_path)

    with pytest.raises(spawn.UpdateScriptMissing):
        spawn.spawn_update()


def test_spawn_detaches_the_update_and_keeps_its_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """A child of the backend would die with it — halfway through a merge."""
    script = tmp_path / spawn.UPDATE_SCRIPT_NAME
    script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    monkeypatch.setattr(spawn.maintenance, "active", lambda: None)
    monkeypatch.setattr(spawn, "project_root", lambda: tmp_path)
    monkeypatch.setattr(spawn, "_log_path", lambda: tmp_path / "logs" / spawn.SPAWN_LOG_NAME)

    calls: list[dict] = []

    class _Popen:
        pid = 777

        def __init__(self, argv, **kwargs):
            calls.append({"argv": argv, **kwargs})

        def poll(self):
            return None

    monkeypatch.setattr(spawn.subprocess, "Popen", _Popen)

    started = spawn.spawn_update()

    assert started.pid == 777
    assert started.log_path.parent.is_dir()
    assert calls[0]["argv"] == ["bash", str(script)]
    assert calls[0]["start_new_session"] is True
    assert calls[0]["cwd"] == str(tmp_path)


def test_spawn_refuses_a_second_update_from_this_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """The flag goes up seconds into the run; two clicks inside that window must not both land."""
    script = tmp_path / spawn.UPDATE_SCRIPT_NAME
    script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    monkeypatch.setattr(spawn.maintenance, "active", lambda: None)
    monkeypatch.setattr(spawn, "project_root", lambda: tmp_path)
    monkeypatch.setattr(spawn, "_log_path", lambda: tmp_path / "logs" / spawn.SPAWN_LOG_NAME)

    class _Running:
        pid = 778

        def __init__(self, argv, **kwargs):
            pass

        def poll(self):
            return None

    monkeypatch.setattr(spawn.subprocess, "Popen", _Running)
    spawn.spawn_update()

    with pytest.raises(spawn.UpdateAlreadyRunning):
        spawn.spawn_update()
