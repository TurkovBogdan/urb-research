"""Набор ENV-ключей, редактируемых страницей настроек.

Это определение полей формы (что показывать, как вводить, когда показывать), а НЕ
запрет: локальное приложение, пользователь сам знает, что меняет. Значения пишутся в
``.env`` как есть, изменения применяются рестартом (Config читается на старте).

``visible_when`` — условие видимости: поле показывается, только когда ТЕКУЩЕЕ значение
другого ключа равно заданному (вычисляется на фронте реактивно от выбора в форме).
Так postgres-поля скрыты при ``DB_PROVIDER=sqlite`` и наоборот.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VisibleWhen:
    """Поле видно, когда значение ``key`` в форме равно ``equals``."""

    key: str
    equals: str


@dataclass(frozen=True)
class SetupField:
    """Одно редактируемое поле: ENV-ключ + рус. название/описание + как вводить."""

    key: str
    group: str
    type: str  # "str" | "int" | "bool" | "choice"
    label: str
    description: str = ""
    choices: tuple[str, ...] = field(default=())
    secret: bool = False
    visible_when: VisibleWhen | None = None


_POSTGRES = VisibleWhen("DB_PROVIDER", "postgres")
_SQLITE = VisibleWhen("DB_PROVIDER", "sqlite")

_DB = "База данных"
_SERVER = "Сервер"
_WORKER = "Фоновые задачи"

FIELDS: tuple[SetupField, ...] = (
    SetupField(
        "DB_PROVIDER", _DB, "choice", "Провайдер БД",
        "postgres — внешний сервер (полноценный); sqlite — локальный файл, без установки",
        choices=("postgres", "sqlite"),
    ),
    SetupField(
        "DB_PATH", _DB, "str", "Файл SQLite",
        "Путь к файлу БД; пусто — runtime/<профиль>/app.sqlite3",
        visible_when=_SQLITE,
    ),
    SetupField(
        "DB_HOST", _DB, "str", "Хост БД",
        "Адрес сервера PostgreSQL", visible_when=_POSTGRES,
    ),
    SetupField(
        "DB_PORT", _DB, "int", "Порт БД",
        "Порт PostgreSQL (обычно 5432)", visible_when=_POSTGRES,
    ),
    SetupField(
        "DB_NAME", _DB, "str", "Имя базы",
        "Название базы данных", visible_when=_POSTGRES,
    ),
    SetupField(
        "DB_USER", _DB, "str", "Пользователь БД",
        "Имя пользователя PostgreSQL", visible_when=_POSTGRES,
    ),
    SetupField(
        "DB_PASSWORD", _DB, "str", "Пароль БД",
        "Пароль пользователя PostgreSQL", secret=True, visible_when=_POSTGRES,
    ),
    SetupField(
        "DB_SSL", _DB, "bool", "TLS для БД",
        "Шифрованное соединение с проверкой сертификата (verify-full)",
        visible_when=_POSTGRES,
    ),
    SetupField(
        "SERVER_HOST", _SERVER, "str", "Хост сервера",
        "Адрес, на котором слушает бэкенд (127.0.0.1 — только локально)",
    ),
    SetupField(
        "SERVER_PORT", _SERVER, "int", "Порт сервера",
        "Порт HTTP-сервера (на нём открывается приложение)",
    ),
    SetupField(
        "SERVER_VITE_PORT", _SERVER, "int", "Порт Vite (разработка)",
        "Порт dev-сервера фронта; нужен только при локальной разработке",
    ),
    SetupField(
        "WORKER_ENABLED", _WORKER, "bool", "Фоновые задачи",
        "Запускать планировщик и выполнение задач в этом же процессе",
    ),
    SetupField(
        "WORKER_TICK_SECONDS", _WORKER, "int", "Интервал планировщика, с",
        "Как часто проверять очередь задач",
    ),
    SetupField(
        "WORKER_MAX_CONCURRENT_RUNS", _WORKER, "int", "Параллельных задач",
        "Максимум одновременно выполняемых задач",
    ),
)

FIELD_BY_KEY: dict[str, SetupField] = {f.key: f for f in FIELDS}


__all__ = ["FIELDS", "FIELD_BY_KEY", "SetupField", "VisibleWhen"]
