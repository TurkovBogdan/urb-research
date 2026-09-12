"""Общие фикстуры тестов и принудительный override на in-memory БД.

Тесты гоняются на SQLite целиком в RAM (``DB_PROVIDER=sqlite``, ``DB_PATH=:memory:``)
— никакого внешнего Postgres-сервера и никаких креды-пулов. Подмена ``DB_*``
env-переменных происходит ДО первых импортов из ``src``, чтобы любой ``Config()``
в любом тесте получил тестовую базу. Это единая точка защиты — нельзя случайно
ударить по dev/prod БД.

Изоляция параллельного прогона бесплатна: каждый xdist-воркер — отдельный
процесс с собственной in-memory базой; схема каждого теста строится из ОРМ-моделей
(``create_all`` в lifespan или в локальной ``db``-фикстуре) на свежем engine.

Heavy-тесты Alembic-миграций (типы колонок ``postgresql.*``) на SQLite не идут —
они скипаются, пока не задан реальный Postgres через ``TEST_PG_DSN``
(``postgresql://user:pass@host:port/dbname``); см. ``pytest_collection_modifyitems``.
База из DSN — только административное подключение: каждому heavy-тесту фикстура
``_own_postgres_database_for_heavy`` создаёт свою одноразовую базу рядом и сносит её после,
а остальные тесты того же прогона остаются на in-memory SQLite.
"""

from __future__ import annotations

# ── Подмена env. Обязательно до импортов из src ─────────────────────────────
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ``TEST_PG_DSN`` (опционально) включает heavy-тесты миграций: не «переводит прогон на
# Postgres», а даёт административное подключение, от которого каждый heavy-тест получает
# свою базу (см. ``_own_postgres_database_for_heavy``). Всё остальное — на in-memory SQLite.
_PG_DSN = os.environ.get("TEST_PG_DSN")
os.environ["DB_PROVIDER"] = "sqlite"
os.environ["DB_PATH"] = ":memory:"
os.environ["DB_SSL"] = "false"

os.environ["WORKER_ENABLED"] = "false"
# Тесты поднимают HTTP API — включаем монтаж зон (дефолт false = worker-only).
os.environ["SERVER_ENABLED"] = "true"
# CORS-origins строятся из server_vite_port; задаём, чтобы preflight-тест видел origin.
os.environ["SERVER_VITE_PORT"] = "13406"
# Тесты пишут все рантайм-артефакты в ``runtime/test/`` (логи, cache, user).
# AppPath читает ``APP_ENV`` → подменяем до первых импортов из src.
os.environ["APP_ENV"] = "test"

# ── Дальше уже можно импортировать src ──────────────────────────────────────
import pytest  # noqa: E402

from src.core.config import Config, get_config  # noqa: E402
from src.core.database import close_database  # noqa: E402
from src.core.loggers import LoggerStore  # noqa: E402

# ── Удобные флаги-алиасы вместо ``-m`` ───────────────────────────────────────
# По умолчанию (без флагов) ``addopts`` оставляет только немаркированные тесты.
# Флаг включает соответствующую группу; несколько флагов объединяются через OR.
# ``--all`` снимает фильтр целиком. Флаги переопределяют ``-m``.
_GROUP_FLAGS = ("pure", "db", "heavy", "live")

# ── Флаги области (путь к тестам) ────────────────────────────────────────────
# Тип теста (marker) и область (каталог) ортогональны: ``--core``/``--module``
# задают ГДЕ искать, marker-флаги — ЧТО запускать. Сахар над позиционными
# путями (``--core`` = ``tests/core tests/apps``) с валидацией имени модуля.
_CORE_PATHS = ("tests/core", "tests/apps")
_MODULES_DIR = _PROJECT_ROOT / "tests" / "modules"


def pytest_addoption(parser):
    group = parser.getgroup("group selection")
    for name in _GROUP_FLAGS:
        group.addoption(
            f"--{name}", action="store_true", default=False,
            help=f"включить тесты, помеченные @pytest.mark.{name}",
        )
    group.addoption(
        "--all", action="store_true", default=False,
        help="запустить все тесты (снять фильтр по меткам)",
    )
    group.addoption(
        "--unmarked", action="store_true", default=False,
        help="только «потерянные» тесты — без метки типа (pure/db/heavy/live)",
    )
    area = parser.getgroup("area selection")
    area.addoption(
        "--core", action="store_true", default=False,
        help="только тесты ядра (tests/core + tests/apps)",
    )
    area.addoption(
        "--module", action="append", default=[], metavar="NAME[,NAME...]",
        help="только тесты модуля tests/modules/NAME; список через запятую "
             "и/или повтор флага",
    )
    # Устарело: in-memory SQLite не имеет пула физических баз, изоляция воркеров
    # бесплатна. Опция оставлена no-op, чтобы старые команды не падали.
    parser.getgroup("xdist").addoption(
        "--dbs", action="store", default=None, metavar="1,3,5-8",
        help="устарело и игнорируется (тесты на in-memory SQLite, пула баз нет)",
    )


def _resolve_area_paths(config) -> list[str]:
    """Каталоги по флагам ``--core``/``--module``; ``[]`` если ни один не задан."""
    if not config.option.core and not config.option.module:
        return []
    if config.option.file_or_dir:
        raise pytest.UsageError(
            "--core/--module нельзя совмещать с явным путём к тестам"
        )
    paths: list[str] = []
    if config.option.core:
        paths.extend(str(_PROJECT_ROOT / p) for p in _CORE_PATHS)
    # ``--module`` принимает список через запятую и может повторяться:
    # ``--module=core_users,core_storage`` ≡ ``--module=core_users --module=core_storage``.
    names = [
        n.strip()
        for spec in config.option.module
        for n in spec.split(",")
        if n.strip()
    ]
    for name in names:
        target = _MODULES_DIR / name
        if not target.is_dir():
            available = sorted(
                p.name for p in _MODULES_DIR.iterdir()
                if p.is_dir() and not p.name.startswith("__")
            )
            raise pytest.UsageError(
                f"неизвестный модуль '{name}'. Доступны: {', '.join(available)}"
            )
        paths.append(str(target))
    return paths


# ── Параллельный запуск ──────────────────────────────────────────────────────
# Каждый xdist-воркер — отдельный процесс с собственной in-memory SQLite, так что
# db/heavy изолированы и параллелятся свободно без какого-либо пула баз.


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config) -> None:
    """По умолчанию распараллеливаем по числу ядер (``-n auto``).

    Ставится здесь, а не в ``pytest_configure``: xdist читает ``numprocesses`` в
    своём ``pytest_cmdline_main`` (раньше ``configure``) и более позднее значение
    не подхватит.

    * ``-n`` не задан → ``-n auto`` (по числу ядер; in-memory БД у каждого своя);
    * явный ``-n``/``-n0`` оставляем как есть (``-n0`` = inprocess для ``--pdb``).

    Внутри воркера ничего не трогаем.
    """
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    if not hasattr(config.option, "numprocesses"):  # xdist не установлен
        return
    if config.option.numprocesses is None:
        config.option.numprocesses = "auto"


def pytest_configure(config):
    area_paths = _resolve_area_paths(config)
    if area_paths:
        config.args[:] = area_paths
    if config.option.all:
        config.option.markexpr = ""
    elif config.option.unmarked:
        # «Потерянные» тесты: ни одной метки типа. Каждый тест обязан нести ровно
        # одну — этот фильтр ловит те, что её не получили (аудит стандарта).
        config.option.markexpr = " and ".join(f"not {n}" for n in _GROUP_FLAGS)
    else:
        chosen = [name for name in _GROUP_FLAGS if getattr(config.option, name)]
        if chosen:
            config.option.markexpr = " or ".join(chosen)


def pytest_collection_modifyitems(config, items):
    """Heavy Alembic-тесты требуют Postgres — скипаем их, пока не задан ``TEST_PG_DSN``.

    Миграции описаны в типах ``postgresql.*`` (JSONB/TIMESTAMP) и на SQLite не
    накатываются.
    """
    if _PG_DSN:
        return
    skip_pg = pytest.mark.skip(
        reason="heavy-тесты миграций требуют Postgres — задай TEST_PG_DSN"
    )
    for item in items:
        if item.get_closest_marker("heavy") is not None:
            item.add_marker(skip_pg)


# ── Изоляция heavy-яруса: база на тест ───────────────────────────────────────

_DISPOSABLE_DATABASE_PREFIX = "urb_test_"


def _postgres_environment(admin_dsn: str, database: str) -> dict[str, str]:
    """``DB_*`` для ``Config``: креды и хост из административного DSN, база — своя."""
    parts = urlsplit(admin_dsn)
    return {
        "DB_PROVIDER": "postgres",
        "DB_HOST": parts.hostname or "127.0.0.1",
        "DB_PORT": str(parts.port or 5432),
        "DB_NAME": database,
        "DB_USER": parts.username or "",
        "DB_PASSWORD": parts.password or "",
        "DB_SSL": "false",
    }


@asynccontextmanager
async def _disposable_database(admin_dsn: str):
    """Свежая база под уникальным именем — создана до блока, снесена после него.

    ``WITH (FORCE)`` рвёт соединения, которые тест мог не закрыть: без этого ``DROP``
    отказывает, и база остаётся висеть на стенде.
    """
    import asyncpg

    database = f"{_DISPOSABLE_DATABASE_PREFIX}{uuid.uuid4().hex[:12]}"
    admin = await asyncpg.connect(admin_dsn)
    try:
        await admin.execute(f'CREATE DATABASE "{database}"')
    finally:
        await admin.close()
    try:
        yield database
    finally:
        admin = await asyncpg.connect(admin_dsn)
        try:
            await admin.execute(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
        finally:
            await admin.close()


@pytest.fixture(autouse=True)
async def _own_postgres_database_for_heavy(request, monkeypatch):
    """Каждый heavy-тест идёт на своей только что созданной базе PostgreSQL.

    Общая база не годится ни в одном режиме: под ``-n auto`` воркеры гоняются за
    ``CREATE TABLE``, под ``-n0`` тест, застемпивший синтетическую ревизию из ``tmp_path``,
    оставляет строку, которую следующий раннер уже не разрешит. База на тест закрывает оба
    случая. Для не-heavy тестов фикстура ничего не делает.
    """
    is_heavy = request.node.get_closest_marker("heavy") is not None
    if not is_heavy or not _PG_DSN:
        yield
        return
    async with _disposable_database(_PG_DSN) as database:
        for key, value in _postgres_environment(_PG_DSN, database).items():
            monkeypatch.setenv(key, value)
        get_config.cache_clear()
        try:
            yield
        finally:
            await close_database()


@pytest.fixture(autouse=True)
def _registry_outside_the_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Реестр процессов — во временный каталог для КАЖДОГО теста.

    `app.main()` объявляет процесс в `runtime/processes/`, а тесты роли зовут именно его: без
    подмены прогон описал бы pytest как процесс установки, и следующий апдейтер на этой машине
    получил бы его в план остановки.
    """
    from src.core import process_registry

    monkeypatch.setattr(process_registry, "project_root", lambda: tmp_path)


@pytest.fixture(autouse=True)
def _reset_logger_store():
    """Сбрасываем каналы между тестами, чтобы один не утекал в другой."""
    yield
    LoggerStore.reset()


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """`get_config` кэширует — между тестами на конфиг сбрасываем lru_cache."""
    get_config.cache_clear()
    yield
    get_config.cache_clear()


@pytest.fixture(autouse=True)
async def _dispose_engine_between_tests(request):
    """Закрываем module-level engine после каждого db-теста.

    На in-memory SQLite чистый старт гарантирован сам собой: каждый db-тест
    (или lifespan) создаёт новый engine через ``init_database`` → новую пустую
    ``:memory:``-базу, а ``init_database`` диспоузит предыдущую. Этот teardown
    лишь подчищает повисший engine, чтобы он не утёк между тестами.

    Пропускается для ``@pytest.mark.pure``: такие тесты БД не трогают.
    """
    yield
    if request.node.get_closest_marker("pure") is not None:
        return
    await close_database()


@pytest.fixture(autouse=True)
def _clear_access_store():
    """Кеш значений доступа живёт в процессе, а база у каждого теста своя.

    Идентификаторы записей повторяются от теста к тесту, поэтому без сброса второй
    тест получил бы значения первого.
    """
    from src.modules.core_connectors.access.store import access_store

    access_store.clear()
    yield
    access_store.clear()


@pytest.fixture
def config() -> Config:
    """Тестовый ``Config`` (in-memory SQLite; у heavy-теста — его одноразовая база PostgreSQL)."""
    return Config()
