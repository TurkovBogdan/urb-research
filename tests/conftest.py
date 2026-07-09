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
"""

from __future__ import annotations

# ── Подмена env. Обязательно до импортов из src ─────────────────────────────
import os
from pathlib import Path
from urllib.parse import urlsplit

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ``TEST_PG_DSN`` (опционально) переводит прогон на реальный Postgres — нужен
# только для heavy-тестов миграций. Без него всё на in-memory SQLite.
_PG_DSN = os.environ.get("TEST_PG_DSN")
if _PG_DSN:
    _u = urlsplit(_PG_DSN)
    os.environ["DB_PROVIDER"] = "postgres"
    os.environ["DB_HOST"] = _u.hostname or "127.0.0.1"
    os.environ["DB_PORT"] = str(_u.port or 5432)
    os.environ["DB_NAME"] = _u.path.lstrip("/")
    os.environ["DB_USER"] = _u.username or ""
    os.environ["DB_PASSWORD"] = _u.password or ""
    os.environ["DB_SSL"] = "false"
else:
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
    """Heavy Alembic-тесты требуют Postgres — скипаем их на in-memory SQLite.

    Миграции описаны в типах ``postgresql.*`` (JSONB/TIMESTAMP) и на SQLite не
    накатываются. Запустить их можно, задав реальную БД через ``TEST_PG_DSN``.
    """
    if Config().db_provider == "postgres":
        return
    skip_pg = pytest.mark.skip(
        reason="heavy-тесты миграций требуют Postgres — задай TEST_PG_DSN"
    )
    for item in items:
        if item.get_closest_marker("heavy") is not None:
            item.add_marker(skip_pg)


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


@pytest.fixture
def config() -> Config:
    """Тестовый ``Config`` (in-memory SQLite либо Postgres из ``TEST_PG_DSN``)."""
    return Config()
