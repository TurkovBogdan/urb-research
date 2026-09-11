"""core/backup: the copy the update refuses to migrate without — both providers.

SQLite is exercised against real files (`VACUUM INTO`, `integrity_check`, a WAL sidecar that a
plain `cp` would miss). PostgreSQL is exercised against stand-in `pg_dump`/`pg_restore` scripts on
`PATH`: this machine has no `postgresql-client`, and what has to be proven here is the argument
construction, the password handling, the verification and the refusals — not that libpq speaks TCP.
A real dump against a real server is rehearsed by hand instead (`tests-migration/tools/pgclient/`
runs the genuine binaries inside the stand's container).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from src.core.backup import (
    POSTGRES_CLIENT_PACKAGE,
    BackupRefused,
    back_up,
    backup_command,
    default_target,
)
from src.core.config import Config

REVISIONS = ("com_004", "rem_005")


def sqlite_config(path: Path) -> Config:
    return Config(db_provider="sqlite", db_path=str(path))


def postgres_config(**over) -> Config:
    settings = dict(
        db_provider="postgres",
        db_host="127.0.0.1",
        db_port=1,
        db_name="research",
        db_user="urb",
        db_password="s3cret",
        db_ssl=False,
    )
    return Config(**{**settings, **over})


def make_database(path: Path, *, rows: int = 3) -> Path:
    connection = sqlite3.connect(path)
    with connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT)")
        connection.executemany(
            "INSERT INTO alembic_version VALUES (?)", [(revision,) for revision in REVISIONS]
        )
        connection.execute("CREATE TABLE note (code TEXT PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO note VALUES (?)", [(f"NOTE_{index}",) for index in range(rows)]
        )
    connection.close()
    return path


def rows_in(path: Path, table: str) -> int:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    finally:
        connection.close()


# ── sqlite ───────────────────────────────────────────────────────────────────

@pytest.mark.pure
def test_sqlite_copy_carries_the_data_and_verifies_itself(tmp_path: Path):
    source = make_database(tmp_path / "app.sqlite3")

    copy = back_up(sqlite_config(source), tmp_path / "copy.sqlite3")

    assert copy.target.exists()
    assert rows_in(copy.target, "note") == 3
    assert copy.revisions == REVISIONS
    assert copy.verification == "integrity_check: ok"
    assert copy.diagnostics == ("foreign_key_check: no violations",)


@pytest.mark.pure
def test_sqlite_copy_includes_what_is_still_in_the_wal_sidecar(tmp_path: Path):
    """The reason this is not `cp`: in WAL mode committed rows live beside the main file until a
    checkpoint, so copying the file alone silently loses them."""
    source = make_database(tmp_path / "app.sqlite3")
    writer = sqlite3.connect(source)
    writer.execute("PRAGMA journal_mode=WAL")
    with writer:
        writer.execute("INSERT INTO note VALUES ('NOTE_in_wal')")
    try:
        assert (source.parent / f"{source.name}-wal").exists()

        copy = back_up(sqlite_config(source), tmp_path / "copy.sqlite3")
    finally:
        writer.close()

    assert rows_in(copy.target, "note") == 4


@pytest.mark.pure
def test_sqlite_default_target_lands_next_to_the_base(tmp_path: Path):
    source = make_database(tmp_path / "app.sqlite3")

    copy = back_up(sqlite_config(source))

    assert copy.target.parent == tmp_path / "backup"
    assert copy.target.name.startswith("app.sqlite3.")
    assert default_target(sqlite_config(source)).parent == tmp_path / "backup"


@pytest.mark.pure
def test_refuses_to_overwrite_an_existing_file(tmp_path: Path):
    source = make_database(tmp_path / "app.sqlite3")
    occupied = tmp_path / "copy.sqlite3"
    occupied.write_text("do not lose me")

    with pytest.raises(BackupRefused) as refusal:
        back_up(sqlite_config(source), occupied)

    assert occupied.read_text() == "do not lose me"
    assert "already exists" in str(refusal.value)


@pytest.mark.pure
def test_refuses_a_missing_database(tmp_path: Path):
    with pytest.raises(BackupRefused) as refusal:
        back_up(sqlite_config(tmp_path / "nothing.sqlite3"), tmp_path / "copy.sqlite3")

    assert "not found" in str(refusal.value)


@pytest.mark.pure
def test_refuses_an_in_memory_base(tmp_path: Path):
    with pytest.raises(BackupRefused) as refusal:
        back_up(sqlite_config(Path(":memory:")), tmp_path / "copy.sqlite3")

    assert ":memory:" in str(refusal.value)


@pytest.mark.pure
def test_the_command_reports_a_refusal_on_stderr_and_exits_nonzero(capsys):
    """The suite itself runs on `DB_PATH=:memory:` — a refusal is exactly the right answer."""
    assert backup_command() == 1
    assert "error:" in capsys.readouterr().err


@pytest.mark.pure
def test_the_command_prints_where_the_copy_went(tmp_path: Path, capsys, monkeypatch):
    source = make_database(tmp_path / "app.sqlite3")
    monkeypatch.setenv("DB_PROVIDER", "sqlite")
    monkeypatch.setenv("DB_PATH", str(source))

    assert backup_command(str(tmp_path / "copy.sqlite3")) == 0
    printed = capsys.readouterr().out
    assert str(tmp_path / "copy.sqlite3") in printed
    assert "integrity_check: ok" in printed
    assert ", ".join(REVISIONS) in printed


# ── postgres ─────────────────────────────────────────────────────────────────

def fake_tool(directory: Path, name: str, body: str) -> None:
    script = directory / name
    script.write_text(f"#!{sys.executable}\nimport json, os, sys\n{body}")
    script.chmod(0o755)


def pg_client(tmp_path: Path, monkeypatch, *, dump_succeeds=True, listing_succeeds=True) -> Path:
    """A `pg_dump`/`pg_restore` pair on PATH that records how it was called."""
    binaries = tmp_path / "bin"
    binaries.mkdir()
    record = tmp_path / "calls.json"
    dump_body = (
        f"record = {str(record)!r}\n"
        "argv = sys.argv[1:]\n"
        "json.dump({'argv': argv, 'password': os.environ.get('PGPASSWORD')}, open(record, 'w'))\n"
        + (
            "target = argv[argv.index('--file') + 1]\n"
            "open(target, 'w').write('PGDMP fake archive')\n"
            if dump_succeeds
            else "sys.stderr.write('connection refused')\nsys.exit(1)\n"
        )
    )
    listing_body = (
        "print(';     Archive created at 2026-09-12')\n"
        "print('215; 1259 16384 TABLE public research urb')\n"
        "print('216; 1259 16385 TABLE public note urb')\n"
        if listing_succeeds
        else "sys.stderr.write('input file appears to be a text format dump')\nsys.exit(1)\n"
    )
    fake_tool(binaries, "pg_dump", dump_body)
    fake_tool(binaries, "pg_restore", listing_body)
    monkeypatch.setenv("PATH", f"{binaries}:{Path(sys.executable).parent}")
    return record


@pytest.mark.pure
def test_postgres_dump_is_custom_format_and_verified_by_pg_restore(tmp_path: Path, monkeypatch):
    record = pg_client(tmp_path, monkeypatch)
    target = tmp_path / "research.dump"

    copy = back_up(postgres_config(), target)

    called = json.loads(record.read_text())
    assert "--format=custom" in called["argv"]
    assert called["argv"][called["argv"].index("--file") + 1] == str(target)
    assert called["argv"][:8] == [
        "--host", "127.0.0.1", "--port", "1", "--username", "urb", "--dbname", "research",
    ]
    assert copy.verification == "pg_restore --list: ok, 2 object(s) in the archive"
    assert copy.source == "urb@127.0.0.1:1/research"


@pytest.mark.pure
def test_postgres_password_travels_in_the_environment_not_in_argv(tmp_path: Path, monkeypatch):
    record = pg_client(tmp_path, monkeypatch)

    back_up(postgres_config(), tmp_path / "research.dump")

    called = json.loads(record.read_text())
    assert called["password"] == "s3cret"
    assert not any("s3cret" in argument for argument in called["argv"])


@pytest.mark.pure
def test_postgres_revisions_degrade_to_nothing_when_the_base_is_unreachable(
    tmp_path: Path, monkeypatch
):
    """Diagnostics never decide: a base that will not tell its heads is still worth copying."""
    pg_client(tmp_path, monkeypatch)

    copy = back_up(postgres_config(), tmp_path / "research.dump")

    assert copy.revisions == ()
    assert "(none read)" in copy.describe()


@pytest.mark.pure
def test_a_failed_dump_leaves_no_half_archive_behind(tmp_path: Path, monkeypatch):
    pg_client(tmp_path, monkeypatch, dump_succeeds=False)
    target = tmp_path / "research.dump"

    with pytest.raises(BackupRefused) as refusal:
        back_up(postgres_config(), target)

    assert target.exists() is False
    assert "pg_dump failed" in str(refusal.value)


@pytest.mark.pure
def test_an_archive_pg_restore_cannot_read_is_not_a_backup(tmp_path: Path, monkeypatch):
    pg_client(tmp_path, monkeypatch, listing_succeeds=False)

    with pytest.raises(BackupRefused) as refusal:
        back_up(postgres_config(), tmp_path / "research.dump")

    assert "pg_restore cannot read the copy" in str(refusal.value)


@pytest.mark.pure
def test_missing_client_binaries_are_a_refusal_not_a_skipped_copy(tmp_path: Path, monkeypatch):
    """The one thing that must never happen: an update migrating because the copy was «optional»."""
    empty = tmp_path / "bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))

    with pytest.raises(BackupRefused) as refusal:
        back_up(postgres_config(), tmp_path / "research.dump")

    assert "pg_dump" in str(refusal.value)
    assert POSTGRES_CLIENT_PACKAGE in str(refusal.value)


@pytest.mark.pure
def test_postgres_default_target_sits_under_the_runtime_root():
    target = default_target(postgres_config())

    assert target.parent.name == "backup"
    assert target.name.startswith("research.")
    assert target.name.endswith(".dump")
