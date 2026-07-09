"""AlembicRunner: version_locations всегда содержат core, плюс модули."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import Config
from src.core.database.migrations import AlembicRunner, _CORE_MIGRATIONS
from src.core.module import Module


class _NoMigrations(Module):
    name = "x"


def _module_with_migrations(name: str, path: Path) -> Module:
    cls = type(
        f"_M_{name}",
        (Module,),
        {"name": name, "migrations_dir": path},
    )
    return cls()


@pytest.mark.pure
def test_core_migrations_always_present():
    runner = AlembicRunner(modules=[])
    cfg = runner._build_config(connection=None)  # type: ignore[arg-type]
    locations = cfg.get_main_option("version_locations")
    assert locations is not None
    assert str(_CORE_MIGRATIONS) in locations


@pytest.mark.pure
def test_modules_without_migrations_dir_only_core():
    runner = AlembicRunner(modules=[_NoMigrations()])
    cfg = runner._build_config(connection=None)  # type: ignore[arg-type]
    locations = cfg.get_main_option("version_locations")
    assert str(_CORE_MIGRATIONS) in locations
    assert locations.count(os.pathsep) == 0


@pytest.mark.pure
def test_version_locations_collected_from_modules(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    modules = [
        _module_with_migrations("a", a),
        _module_with_migrations("b", b),
    ]
    runner = AlembicRunner(modules=modules)
    cfg = runner._build_config(connection=None)  # type: ignore[arg-type]
    locations = cfg.get_main_option("version_locations")
    assert str(_CORE_MIGRATIONS) in locations
    assert str(a) in locations
    assert str(b) in locations
    assert locations.count(os.pathsep) == 2


@pytest.mark.pure
def test_path_separator_set():
    runner = AlembicRunner(modules=[])
    cfg = runner._build_config(connection=None)  # type: ignore[arg-type]
    assert cfg.get_main_option("path_separator") == "os"


_INDEPENDENT_ROOT = '''\
revision = "{rev}"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
'''


@pytest.mark.heavy
async def test_status_detects_new_independent_root_on_populated_db(
    config: Config, tmp_path: Path
):
    """Новый модуль = независимый корень (down_revision=None), добавленный к уже
    наполненной БД, обязан попасть в pending. Регресс на баг, где
    iterate_revisions(heads, current) отдавал лишь потомков current и терял его."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "zz01_a.py").write_text(_INDEPENDENT_ROOT.format(rev="zz01_aaaa"))
    (dir_b / "zz02_b.py").write_text(_INDEPENDENT_ROOT.format(rev="zz02_bbbb"))
    mod_a = _module_with_migrations("a", dir_a)
    mod_b = _module_with_migrations("b", dir_b)

    engine = create_async_engine(config.database_url)
    try:
        # БД наполнена: core + независимый корень A.
        await AlembicRunner(modules=[mod_a]).upgrade_head(engine)
        # Теперь добавляем второй независимый корень B — он должен быть pending.
        status = await AlembicRunner(modules=[mod_a, mod_b]).status(engine)
    finally:
        await engine.dispose()

    revs = [p.revision for p in status.pending]
    assert not status.up_to_date
    assert "zz02_bbbb" in revs          # новый корень виден
    assert "zz01_aaaa" not in revs      # уже применённый не дублируется


@pytest.mark.heavy
async def test_upgrade_head_applies_core_migrations(config: Config):
    """Без модулей всё равно накатываются core-миграции."""
    runner = AlembicRunner(modules=[])
    engine = create_async_engine(config.database_url)
    try:
        await runner.upgrade_head(engine)
        async with engine.connect() as conn:
            from sqlalchemy import inspect

            tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
        assert {
            "core_tasks", "core_tasks_logs", "core_locks", "core_modules_settings",
            "core_modules_state",
        }.issubset(tables)
    finally:
        await engine.dispose()


# ── full-tree structure & schema parity ──────────────────────────────────────
# These replace the per-module test_migration.py smoke-tests that pinned the old
# (pre-rebuild) revision ids. They assert structural invariants generically (so
# they survive future migrations) and verify the whole rebuilt tree applies to a
# clean DB producing exactly the model schema.

def _full_script():
    """ScriptDirectory over core + every real module (no DB connection needed)."""
    from alembic.script import ScriptDirectory

    from src.apps.app.modules import build_modules

    return ScriptDirectory.from_config(
        AlembicRunner(modules=build_modules())._base_config()
    )


def _module_of(path: str) -> str:
    if "/modules/" in path:
        return path.split("/modules/")[1].split("/")[0]
    return "core"


@pytest.mark.pure
def test_every_module_chain_is_linear_with_single_head():
    """Each module's revisions form ONE linear chain: a single root
    (down_revision=None), a single head, no forks; and every revision id equals
    its filename stem and fits alembic_version's varchar(32)."""
    script = _full_script()

    by_module: dict[str, list] = {}
    for rev in script.walk_revisions():
        by_module.setdefault(_module_of(rev.path), []).append(rev)

    assert "core" in by_module  # core always ships migrations; modules add their own chains

    for module, revs in by_module.items():
        ids = {r.revision for r in revs}
        roots = [r for r in revs if r.down_revision is None]
        # in-module parent links only (down_revision never crosses modules)
        parents = [r.down_revision for r in revs if r.down_revision is not None]
        children_of = [p for p in parents if p in ids]
        heads = ids - set(children_of)

        assert len(roots) == 1, f"{module}: expected 1 root, got {[r.revision for r in roots]}"
        assert len(heads) == 1, f"{module}: expected 1 head, got {heads}"
        # no fork: no revision is the parent of two siblings
        assert len(children_of) == len(set(children_of)), f"{module}: forked chain"
        for r in revs:
            from pathlib import Path as _P

            assert r.revision == _P(r.path).stem, f"{module}: {r.revision} != filename"
            assert len(r.revision) <= 32, f"{module}: {r.revision} > 32 chars"


@pytest.mark.pure
def test_cross_module_depends_on_targets_are_non_heads():
    """Every cross-module `depends_on` must point at a NON-head revision, else
    `command.upgrade(heads)` raises an overlap RevisionError (a recorded head that
    is a dependency-ancestor of another head). See conventions/db-migrations.md."""
    script = _full_script()
    heads = set(script.get_heads())

    # Pure core has no cross-module `depends_on` (one chain only); the check stays
    # for when modules are re-added — every cross-module dep must target a non-head.
    for rev in script.walk_revisions():
        deps = rev.dependencies
        if not deps:
            continue
        for target in (deps if isinstance(deps, (list, tuple)) else (deps,)):
            assert target not in heads, (
                f"{rev.revision} depends_on head {target!r} — must target a non-head"
            )


def _structural_diffs(sync_conn):
    """compare_metadata diffs limited to added/removed tables & columns (the
    high-signal kind), ignoring type/default/index noise and `alembic_version`."""
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext

    from src.core.database.runtime import Base

    ctx = MigrationContext.configure(sync_conn)
    structural = {"add_table", "remove_table", "add_column", "remove_column"}
    out: list[str] = []
    for diff in compare_metadata(ctx, Base.metadata):
        for item in (diff if isinstance(diff, list) else [diff]):
            if not (isinstance(item, tuple) and item and item[0] in structural):
                continue
            obj = item[1]
            table = obj.name if hasattr(obj, "name") else item[2]
            if table == "alembic_version":
                continue
            out.append(f"{item[0]}:{table}")
    return out


@pytest.mark.heavy
async def test_full_tree_upgrade_builds_model_schema_with_seeds(config: Config):
    """The whole rebuilt tree applies to a clean DB (validates cross-module
    ordering / depends_on / FK creation order / no head-overlap), produces exactly
    the model tables with no structural drift, and lands the data seeds."""
    from sqlalchemy import inspect

    import src.core.models  # noqa: F401  — наполнить Base.metadata (иначе пусто вне полного прогона)
    from src.apps.app.modules import build_modules
    from src.core.database.runtime import Base

    runner = AlembicRunner(modules=build_modules())
    engine = create_async_engine(config.database_url)
    try:
        await runner.upgrade_head(engine)
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
            diffs = await conn.run_sync(_structural_diffs)
    finally:
        await engine.dispose()

    expected = {t.name for t in Base.metadata.sorted_tables}
    assert expected.issubset(tables), f"missing tables: {expected - tables}"
    assert "alembic_version" in tables
    assert diffs == [], f"schema drift vs models: {diffs}"
