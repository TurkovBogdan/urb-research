"""Application config loaded from .env via pydantic-settings.

Naming: this layer is called ``Config`` (deploy-time, env-backed, read-only).
Runtime user-tunable parameters live in ``src.core.settings`` and the
``core_modules_settings`` table.
"""

from __future__ import annotations

import ssl
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.pool import StaticPool

from src.core.app_path import resolve_runtime_root


def _app_root() -> Path:
    """Корень приложения: папка рядом с бинарём (frozen) либо корень проекта."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _env_file() -> Path:
    """`.env` рядом с бинарём в frozen-режиме, иначе — в корне проекта."""
    return _app_root() / ".env"


class Config(BaseSettings):
    """Core-конфиг приложения. Модули регистрируют свои ``*Config`` отдельно."""

    model_config = SettingsConfigDict(
        env_file=_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── APP — идентичность процесса ────────────────────────────────────────
    # APP_ENV выбирает runtime/<env>/ (читается и напрямую в app_path.py, до
    # Config) и несёт ось dev/test/prod. Поведение по нему НЕ ветвится — только
    # выбор рантайм-директории (reload/CORS — это явные SERVER_*).
    app_env: str = "prod"
    app_log_level: str = "INFO"

    # ── SERVER — HTTP-транспорт (общий для зон internal/external/webhook) ────
    # SERVER_ENABLED — поднимать ли HTTP-сервер. По умолчанию ВЫКЛ: процесс может
    # работать как «только worker» (lifespan жив, HTTP-маршруты не монтируются).
    # CLI-флаг --backend перекрывает (флаг > env).
    server_enabled: bool = False
    server_host: str = "127.0.0.1"
    server_port: int = 13410
    # Hot-reload на изменении исходников (src/), общий ключ для обеих поверхностей:
    # SERVER → uvicorn --reload; чистый WORKER → watchfiles-рестарт подпроцесса.
    # Только dev; НЕсовместим с server_processes>1 (reload-супервизор держит один
    # процесс). CLI-флаг --hot-reload/--no-hot-reload перекрывает.
    server_hot_reload: bool = False
    # Число процессов uvicorn (НЕ фоновый worker — это про HTTP, см. WORKER_*).
    # 1 — один процесс; >1 занимает несколько ядер (тогда миграции — только через
    # `src/app.py migrate`, а планировщик — в worker-процессе, см. WORKER_ENABLED).
    # Игнорируется при server_hot_reload=true.
    server_processes: int = 1
    # Порт Vite dev-сервера: нужен только для dev-CORS (origins ниже). Пусто = прод
    # (фронт раздаёт nginx, CORS не нужен). Тот же порт читает web/vite.config.ts.
    server_vite_port: int | None = None
    # DEBUG-only: искусственная задержка (мс) на КАЖДЫЙ запрос зоны internal — для
    # отладки фронта (скелетоны/лоадеры). 0 = выкл: зон-зависимость не монтируется
    # вовсе (нулевой оверхед). CLI-флаг --debug-delay перекрывает. В проде держать 0.
    server_debug_delay_ms: int = 0

    # ── MCP — поверхность модулей как MCP-серверов (зона /mcp) ──────────────
    # Допустимые Host-заголовки для смонтированных MCP-серверов (CSV): защита от
    # DNS-rebinding на ASGI-слое (TrustedHostMiddleware). Пусто = без проверки
    # (dev/localhost, либо Host фильтрует nginx по server_name). В проде за nginx
    # задать публичный хост(ы). Форк fastmcp не имеет bundled TransportSecuritySettings.
    mcp_allowed_hosts: str = ""

    @property
    def mcp_allowed_hosts_list(self) -> list[str]:
        """``mcp_allowed_hosts`` (CSV) → список; пусто → ``[]`` (проверка выключена)."""
        return [h.strip() for h in self.mcp_allowed_hosts.split(",") if h.strip()]

    # Статичный bearer-токен MCP-серверов (черновой auth до auth-модуля): резолвер
    # модуля сверяет предъявленный токен с этим значением. Пусто = локальный режим
    # без проверки (allow-all, dev/localhost). В проде задать непустым.
    mcp_token: str = ""

    # ── MCP stdio-шим (клиент спавнит нас как command-сервер) ──────────────
    # Роль `--mcp-stdio`: MCP-клиент запускает процесс по stdio, шим лениво
    # поднимает backend и мостит вызовы на его /mcp/<code>. Ничего не крутится в
    # покое; backend переживает шим (гасят вручную). См. apps/app/mcp_stdio.py.
    # Открывать системный браузер на главной, когда backend реально подняли.
    mcp_stdio_open_browser: bool = True
    # Поднимать ли worker (планировщик) вместе с backend. Ресёрч/поиск синхронны —
    # по умолчанию не нужен; включить, если появятся фоновые задачи.
    mcp_stdio_start_worker: bool = False
    # Сколько секунд ждать готовности backend (/internal/health) после спавна.
    mcp_stdio_boot_timeout: int = 30
    # Код проксируемого MCP-сервера. Пусто → единственный смонтированный модулями.
    mcp_stdio_code: str = ""

    # ── DATABASE: provider ─────────────────────────────────────────────────
    # sqlite — по умолчанию: zero-install (без сервера, один файл). postgres —
    # опция для боевого масштаба (pgvector), требует DB_HOST/DB_NAME/DB_USER/DB_PASSWORD.
    db_provider: Literal["postgres", "sqlite"] = "sqlite"
    # SQLite-файл (только при db_provider=sqlite). Пусто → <runtime_root>/app.sqlite3.
    db_path: str = ""

    # ── DATABASE: postgres connection ──────────────────────────────────────
    # Обязательны при db_provider=postgres; при sqlite игнорируются (см. _validate_db).
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_echo: bool = False

    # TLS. ``db_ssl=True`` → строго verify-full по CA из ``db_cert``
    # (шифрование + проверка цепочки + сверка hostname). ``db_cert`` —
    # путь к CA-файлу от корня приложения; обязателен при ``db_ssl``.
    # ``db_client_cert``/``db_client_key`` — клиентский сертификат для mutual
    # TLS (сервер с ``clientcert=verify-full``); задаются парой или не задаются.
    db_ssl: bool = True
    db_cert: str | None = None
    db_client_cert: str | None = None
    db_client_key: str | None = None

    # Сетевые таймауты и пул соединений (критично для удалённой БД).
    db_connect_timeout: int = 10
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_recycle: int = 1800
    db_pool_timeout: int = 30

    # Потолок времени на ОДИН запрос (asyncpg command_timeout). 0 = без лимита.
    # Внимание: применяется и к миграциям при старте — большое значение/0, если
    # есть тяжёлые DDL. Защищает пул от «зависших» соединений на нестабильном
    # удалённом канале.
    db_command_timeout: int = 0
    # Проверка живости соединения перед выдачей из пула (+1 RTT на checkout).
    # На удалёнке для фоновых задач оправдана; выключить, если RTT велик и линк
    # стабилен (тогда от обрывов спасает db_pool_recycle + keepalive).
    db_pool_pre_ping: bool = True
    # TCP keepalive в сторону PG: держит NAT-маппинг и быстрее ловит мёртвый
    # peer на удалённом канале. 0 = не задавать (системный дефолт PG, ~2 ч).
    db_tcp_keepalives_idle: int = 60

    # ── WORKER — фон: планировщик + выполнение задач ───────────────────────
    # WORKER_ENABLED — поднимать ли тикер в этом процессе. dev ставит true (один
    # процесс держит веб + задачи); prod-web = false (фон в отдельном worker-
    # процессе). CLI-флаг --worker перекрывает (флаг > env).
    worker_enabled: bool = False
    # Scope воркера: CSV имён модулей, чьи задачи гоняет этот процесс; пусто = все.
    worker_modules: str = ""
    # Ручки движка планировщика — общие для встроенного (dev) и worker-процесса.
    worker_tick_seconds: int = 5
    # Потолок одновременно выполняемых задач (asyncio.Semaphore в Ticker).
    # Согласуй с пулом БД: каждая задача держит ≥1 соединение, так что
    # значение > (db_pool_size + db_max_overflow) упрётся в db_pool_timeout.
    worker_max_concurrent_runs: int = 10

    # Накатывать Alembic-миграции при старте. Отключается в dev-watch
    # (uvicorn --reload), чтобы reload не накатил недописанную миграцию;
    # см. src/core/database/README.md.
    db_auto_migrate: bool = True

    @property
    def worker_modules_set(self) -> frozenset[str] | None:
        """``worker_modules`` (CSV) → frozenset; пусто → None (все модули)."""
        names = {n.strip() for n in self.worker_modules.split(",") if n.strip()}
        return frozenset(names) or None

    @property
    def cors_origins(self) -> list[str]:
        """Dev-CORS origins для Vite. Пусто, если server_vite_port не задан (прод)."""
        if self.server_vite_port is None:
            return []
        return [
            f"http://localhost:{self.server_vite_port}",
            f"http://127.0.0.1:{self.server_vite_port}",
        ]

    @model_validator(mode="after")
    def _validate_db(self) -> "Config":
        if self.db_provider == "postgres":
            missing = [
                name.upper()
                for name in ("db_host", "db_name", "db_user", "db_password")
                if not getattr(self, name)
            ]
            if missing:
                raise ValueError(
                    f"DB_PROVIDER=postgres requires: {', '.join(missing)}"
                )
            if self.db_ssl and not self.db_cert:
                raise ValueError("DB_CERT required when DB_SSL is enabled")
        if bool(self.db_client_cert) != bool(self.db_client_key):
            raise ValueError("DB_CLIENT_CERT and DB_CLIENT_KEY must be set together")
        return self

    @property
    def sqlite_in_memory(self) -> bool:
        """SQLite целиком в RAM: ``DB_PROVIDER=sqlite`` + ``DB_PATH=:memory:``.

        База живёт в рамках одного соединения, поэтому ниже включается StaticPool
        (см. ``engine_kwargs``). Используется тестами вместо физического Postgres.
        """
        return self.db_provider == "sqlite" and self.db_path == ":memory:"

    def _sqlite_path(self) -> Path:
        """Файл SQLite-БД: ``db_path`` (если задан) или ``<runtime_root>/app.sqlite3``."""
        if self.db_path:
            return self._resolve(self.db_path)
        return resolve_runtime_root() / "app.sqlite3"

    @property
    def database_url(self) -> str:
        if self.db_provider == "sqlite":
            if self.sqlite_in_memory:
                return "sqlite+aiosqlite://"
            return f"sqlite+aiosqlite:///{self._sqlite_path()}"
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def engine_kwargs(self) -> dict[str, Any]:
        """``create_async_engine`` kwargs (пул + connect_args) под текущий провайдер.

        SQLite — один писатель: пул не тюним, отдаём busy-timeout на соединение.
        In-memory SQLite живёт внутри одного коннекта — StaticPool держит его
        единственным и общим для всех сессий engine'а (иначе каждая новая сессия
        получила бы свою пустую БД).
        Postgres — пул и (опц.) verify-full TLS из ``db_connect_args``.
        """
        if self.db_provider == "sqlite":
            connect_args: dict[str, Any] = {"timeout": self.db_connect_timeout}
            if self.sqlite_in_memory:
                connect_args["check_same_thread"] = False
                return {"connect_args": connect_args, "poolclass": StaticPool}
            return {"connect_args": connect_args}
        return {
            "pool_pre_ping": self.db_pool_pre_ping,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_recycle": self.db_pool_recycle,
            "pool_timeout": self.db_pool_timeout,
            "connect_args": self.db_connect_args,
        }

    @property
    def db_connect_args(self) -> dict[str, Any]:
        """asyncpg connect-args для engine: connect-таймаут и (опц.) verify-full TLS.

        При заданных ``db_client_cert``/``db_client_key`` контекст несёт ещё и
        клиентский сертификат (mutual TLS).
        """
        # jit=off — PG JIT добавляет десятки мс к коротким OLTP-запросам синков.
        server_settings: dict[str, str] = {"jit": "off"}
        if self.db_tcp_keepalives_idle:
            server_settings["tcp_keepalives_idle"] = str(self.db_tcp_keepalives_idle)
        args: dict[str, Any] = {
            "timeout": self.db_connect_timeout,
            "server_settings": server_settings,
        }
        if self.db_command_timeout:
            args["command_timeout"] = self.db_command_timeout
        if self.db_ssl:
            ctx = ssl.create_default_context(cafile=str(self._resolve(self.db_cert)))
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
            if self.db_client_cert:
                ctx.load_cert_chain(
                    certfile=str(self._resolve(self.db_client_cert)),
                    keyfile=str(self._resolve(self.db_client_key)),
                )
            args["ssl"] = ctx
        return args

    @staticmethod
    def _resolve(path: str) -> Path:
        """Путь к файлу: абсолютный как есть, относительный — от корня приложения."""
        p = Path(path)
        return p if p.is_absolute() else _app_root() / p


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Кэшированный инстанс. Используется apps/* и тестами через override."""
    return Config()


__all__ = ["Config", "get_config"]
