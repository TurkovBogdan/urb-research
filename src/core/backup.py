"""A copy of the database, taken before anything is allowed to migrate it.

Shipped code on purpose. `AGENTS/` is not in git, so a tool that lives only in a developer's
checkout is absent exactly where the copy matters most: on a live install, after the merge, with
the old schema still under the new code.

**SQLite.** Copying the file (`cp`) is a documented way to obtain a corrupt copy: it reads the
file linearly while a writer rewrites pages it has already passed. In WAL mode a second hazard is
added — committed data sits in the sidecar until a checkpoint, so a copy of the main file alone
silently lags. `VACUUM INTO` takes a consistent snapshot under a read transaction and lands it as
a single file with no sidecars. The copy is verified immediately: `integrity_check` must answer
`ok`. `foreign_key_check` is reported separately — reference checking is off in the application,
so its findings are diagnostics, not a failed copy.

Restoring SQLite: put the copy in place of the main file only together with deleting the stale
`-wal`/`-shm` next to it, or the engine replays a foreign journal over it.

**PostgreSQL.** `pg_dump --format=custom` is a snapshot under a single read transaction —
consistent on a live base and selectively restorable. Verification is `pg_restore --list`: it
parses the archive's table of contents and fails on a truncated or corrupt file, which is the
role `integrity_check` plays for SQLite. The password travels in `PGPASSWORD`, not on a command
line that the process table shows to everyone. A missing `pg_dump`/`pg_restore` is a refusal
naming `postgresql-client`, never a silent skip: an update may not migrate blind.

Restoring PostgreSQL: `pg_restore --clean --if-exists -d <database> <file>`; the database must
exist, the objects inside are recreated.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from collections.abc import Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.core.app_path import project_root, resolve_runtime_root
from src.core.config import Config

DUMP_TIMEOUT_SECONDS = 3600
FOREIGN_KEY_VIOLATIONS_SHOWN = 10
POSTGRES_CLIENT_PACKAGE = "postgresql-client"

_ALEMBIC_HEADS = "SELECT version_num FROM alembic_version"
_STAMP_FORMAT = "%Y%m%d-%H%M%S"


class BackupRefused(RuntimeError):
    """No copy was taken; the message is what the operator reads."""


@dataclass(frozen=True)
class Backup:
    """A copy that exists and has passed its verification."""

    source: str
    target: Path
    revisions: tuple[str, ...]
    verification: str
    diagnostics: tuple[str, ...] = ()

    def describe(self) -> str:
        return "\n".join(
            [
                f"source:    {self.source}",
                f"copy:      {self.target} ({_megabytes(self.target)})",
                f"revisions: {', '.join(self.revisions) or '(none read)'}",
                f"verified:  {self.verification}",
                *self.diagnostics,
            ]
        )


def default_target(config: Config) -> Path:
    """Where a copy lands when the caller names no path: next to a file base, otherwise under
    the runtime root of this profile."""
    stamp = datetime.now().strftime(_STAMP_FORMAT)
    if config.db_provider == "sqlite":
        source = sqlite_source(config)
        return source.parent / "backup" / f"{source.name}.{stamp}"
    return resolve_runtime_root() / "backup" / f"{config.db_name}.{stamp}.dump"


def back_up(config: Config, target: Path | None = None) -> Backup:
    """Take the copy and verify it, or refuse. Never overwrites an existing file."""
    resolved = _prepare_target(target if target is not None else default_target(config))
    if config.db_provider == "sqlite":
        return _back_up_sqlite(config, resolved)
    return _back_up_postgres(config, resolved)


def sqlite_source(config: Config) -> Path:
    """The file the APP opens — resolved by `Config`, runtime root and all, so that a copy can
    never be of a base nobody serves."""
    source = config.sqlite_file
    if source is None:
        raise BackupRefused("DB_PATH=:memory: — there is nothing on disk to copy")
    return source


def backup_command(target: str | None = None) -> int:
    """`app.py backup [path]`: the report on stdout, a refusal on stderr and exit 1."""
    try:
        backup = back_up(Config(), Path(target) if target else None)
    except BackupRefused as refusal:
        print(f"error: {refusal}", file=sys.stderr)
        return 1
    print(backup.describe())
    return 0


def main(argv: Sequence[str]) -> int:
    return backup_command(argv[0] if argv else None)


def _prepare_target(target: Path) -> Path:
    resolved = target.expanduser()
    if not resolved.is_absolute():
        resolved = project_root() / resolved
    if resolved.exists():
        raise BackupRefused(f"the file already exists, refusing to overwrite it: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _back_up_sqlite(config: Config, target: Path) -> Backup:
    source = sqlite_source(config)
    if not source.exists():
        raise BackupRefused(f"database file not found: {source}")

    with closing(sqlite3.connect(f"file:{source}?mode=ro", uri=True)) as base:
        revisions = _sqlite_revisions(base)
        base.execute("VACUUM INTO ?", (str(target),))
    with closing(sqlite3.connect(f"file:{target}?mode=ro", uri=True)) as copy:
        integrity = copy.execute("PRAGMA integrity_check").fetchone()[0]
        violations = copy.execute("PRAGMA foreign_key_check").fetchall()

    if integrity != "ok":
        raise BackupRefused(f"the copy failed its integrity check ({integrity}): {target}")
    return Backup(
        source=f"{source} ({_megabytes(source)})",
        target=target,
        revisions=revisions,
        verification=f"integrity_check: {integrity}",
        diagnostics=_foreign_key_report(violations),
    )


def _sqlite_revisions(connection: sqlite3.Connection) -> tuple[str, ...]:
    """Alembic heads as of the copy — one per branch (core + modules)."""
    try:
        rows = connection.execute(_ALEMBIC_HEADS).fetchall()
    except sqlite3.DatabaseError:
        return ()
    return tuple(sorted(row[0] for row in rows))


def _foreign_key_report(violations: Sequence[tuple]) -> tuple[str, ...]:
    if not violations:
        return ("foreign_key_check: no violations",)
    listed = [
        f"  {child_table} rowid={rowid} → {parent_table} (constraint #{ordinal})"
        for child_table, rowid, parent_table, ordinal in violations[:FOREIGN_KEY_VIOLATIONS_SHOWN]
    ]
    hidden = len(violations) - FOREIGN_KEY_VIOLATIONS_SHOWN
    tail = [f"  … and {hidden} more"] if hidden > 0 else []
    return (f"foreign_key_check: {len(violations)} violation(s)", *listed, *tail)


def _back_up_postgres(config: Config, target: Path) -> Backup:
    pg_dump = _require_tool("pg_dump")
    pg_restore = _require_tool("pg_restore")
    revisions = _postgres_revisions(config)
    environment = _postgres_environment(config)

    dump = _run(
        [pg_dump, *_postgres_connection(config), "--format=custom", "--file", str(target)],
        environment,
    )
    if dump.returncode != 0:
        target.unlink(missing_ok=True)
        raise BackupRefused(f"pg_dump failed:\n{dump.stderr.strip()}")

    listing = _run([pg_restore, "--list", str(target)], environment)
    if listing.returncode != 0:
        raise BackupRefused(f"pg_restore cannot read the copy:\n{listing.stderr.strip()}")
    archived = sum(1 for line in listing.stdout.splitlines() if line and not line.startswith(";"))
    return Backup(
        source=f"{config.db_user}@{config.db_host}:{config.db_port}/{config.db_name}",
        target=target,
        revisions=revisions,
        verification=f"pg_restore --list: ok, {archived} object(s) in the archive",
    )


def _require_tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise BackupRefused(
            f"{name} is not in PATH — install {POSTGRES_CLIENT_PACKAGE} "
            f"(no older than the server, or {name} refuses to run at all)"
        )
    return found


def _postgres_connection(config: Config) -> list[str]:
    return [
        "--host", config.db_host,
        "--port", str(config.db_port),
        "--username", config.db_user,
        "--dbname", config.db_name,
    ]


def _postgres_environment(config: Config) -> dict[str, str]:
    environment = dict(os.environ)
    if config.db_password:
        environment["PGPASSWORD"] = config.db_password
    return environment


def _postgres_revisions(config: Config) -> tuple[str, ...]:
    """Alembic heads through asyncpg — the same answer the SQLite branch reads from the file.

    Diagnostics only: a base that will not tell its revisions is still worth copying, so every
    failure here degrades to «none read» instead of refusing the copy.
    """
    try:
        import asyncio

        import asyncpg
    except ImportError:
        return ()

    async def read() -> tuple[str, ...]:
        connection = await asyncpg.connect(
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password or None,
            database=config.db_name,
            ssl=config.db_connect_args.get("ssl"),
            timeout=config.db_connect_timeout,
        )
        try:
            rows = await connection.fetch(_ALEMBIC_HEADS)
        finally:
            await connection.close()
        return tuple(sorted(row["version_num"] for row in rows))

    try:
        return asyncio.run(read())
    except Exception:  # noqa: BLE001
        return ()


def _run(argv: list[str], environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            env=environment,
            capture_output=True,
            text=True,
            timeout=DUMP_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as failure:
        raise BackupRefused(f"`{' '.join(argv)}` could not run: {failure}") from failure


def _megabytes(path: Path) -> str:
    return f"{path.stat().st_size / 1024 / 1024:.1f} MB"


__all__ = [
    "Backup",
    "BackupRefused",
    "back_up",
    "backup_command",
    "default_target",
    "main",
    "sqlite_source",
]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
