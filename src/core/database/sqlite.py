"""Настройки движка SQLite: прагмы соединения и намерение транзакции.

Ставятся на событии ``connect``, а не один раз при старте: настройки уровня
соединения не переживают переподключение, а пул выдаёт то новые соединения, то
переиспользованные. Под асинхронным движком слушатель вешается на
``engine.sync_engine`` — на сам ``AsyncEngine`` его повесить нельзя.

``journal_mode`` пишется в заголовок файла базы (повтор на каждом соединении
безвреден), остальные ручки живут внутри соединения. Режим журнала — не команда,
а запрос: он возвращает **фактически** установившийся режим, и переключение может
не произойти без всякой ошибки, поэтому результат читается и расхождение уходит
в лог.

Прагмы ожидания блокировки здесь нет намеренно: ``busy_timeout`` задаёт параметр
``timeout`` драйвера (``Config.engine_kwargs``). ``synchronous = NORMAL`` —
осознанный выбор долговечности: в режиме WAL падение приложения не теряет
закоммиченного, разница с ``FULL`` проявляется только при крахе ОС.

**Намерение транзакции.** Транзакция, начавшаяся с чтения, не может стать пишущей:
её снимок мог разойтись с базой, и движок отказывает — причём на неблокирующей
блокировке, мимо ``busy_timeout``, так что повтор не помогает. Поэтому пишущая
транзакция объявляет себя пишущей при открытии: драйверу запрещается печатать
``BEGIN`` самому (``isolation_level = None``), а на событии ``begin`` печатается
``BEGIN IMMEDIATE`` тем транзакциям, что помечены ``WRITE_EXECUTION_OPTIONS``
(их ставит ``database.write_scope``). Забытая пометка ловится сторожем: изменяющий
оператор в читающей транзакции — ошибка, а не тихая мина. Сторож работает на любой
базе, перехват открытия — только на файловой (почему — у самого перехвата).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config import Config
from src.core.loggers import get_logger

_LOG = get_logger()

_JOURNAL_MODE = "wal"
_VIOLATIONS_IN_MESSAGE = 10
_WRITE_OPTION = "writing_transaction"
_REPORTED_PRAGMAS = ("journal_mode", "synchronous", "foreign_keys")
_MUTATING_STATEMENTS = ("INSERT", "UPDATE", "DELETE", "REPLACE")

WRITE_EXECUTION_OPTIONS = {_WRITE_OPTION: True}

_CONNECTION_PRAGMAS: tuple[str, ...] = (
    "PRAGMA foreign_keys = ON",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA cache_size = -64000",
    "PRAGMA journal_size_limit = 67108864",
)


def connection_pragmas(config: Config) -> tuple[str, ...]:
    """Прагмы, которые получает каждое новое соединение при текущем провайдере.

    База в памяти режим журнала не запрашивает: она всегда отвечает ``memory``,
    и просить у неё WAL — гарантированное расхождение в логе.
    """
    if config.db_provider != "sqlite":
        return ()
    if config.sqlite_in_memory:
        return _CONNECTION_PRAGMAS
    return (f"PRAGMA journal_mode = {_JOURNAL_MODE.upper()}", *_CONNECTION_PRAGMAS)


def configure_sqlite(engine: AsyncEngine, config: Config) -> None:
    """Навесить настройки SQLite на движок; для остальных провайдеров — ничего."""
    pragmas = connection_pragmas(config)
    if not pragmas:
        return
    expected_journal_mode = None if config.sqlite_in_memory else _JOURNAL_MODE

    reported = False

    @event.listens_for(engine.sync_engine, "connect")
    def apply_connection_pragmas(dbapi_connection, connection_record) -> None:
        nonlocal reported
        cursor = dbapi_connection.cursor()
        try:
            for statement in pragmas:
                cursor.execute(statement)
                cursor.fetchall()
            effective = {name: _read(cursor, name) for name in _REPORTED_PRAGMAS}
            if not reported:
                # Умолчания задаются при сборке движка, поэтому в лог идут снятые
                # значения, а не те, что мы просили.
                _LOG.info("sqlite: %s", effective)
                reported = True
            if expected_journal_mode is None:
                return
            if str(effective["journal_mode"]).lower() != expected_journal_mode:
                _LOG.warning(
                    "sqlite: журнал не переключился — запрошен %s, действует %s",
                    expected_journal_mode,
                    effective["journal_mode"],
                )
        finally:
            cursor.close()

    # База в памяти живёт в одном соединении драйвера (StaticPool), общем для всех
    # сессий: перехватывать открытие транзакции там нельзя — вторая сессия получит
    # «cannot start a transaction within a transaction». Единственного писателя в
    # памяти и так нет, объявлять намерение не перед кем.
    if not config.sqlite_in_memory:

        @event.listens_for(engine.sync_engine, "connect")
        def take_over_transaction_start(dbapi_connection, connection_record) -> None:
            dbapi_connection.isolation_level = None

        @event.listens_for(engine.sync_engine, "begin")
        def begin_with_declared_intent(connection: Connection) -> None:
            writing = connection.get_execution_options().get(_WRITE_OPTION, False)
            connection.exec_driver_sql("BEGIN IMMEDIATE" if writing else "BEGIN")

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def require_declared_write_intent(
        connection: Connection, cursor, statement, parameters, context, executemany
    ) -> None:
        if not statement.lstrip().upper().startswith(_MUTATING_STATEMENTS):
            return
        if connection.get_execution_options().get(_WRITE_OPTION, False):
            return
        raise RuntimeError(
            "sqlite: изменяющий оператор в читающей транзакции — используй write_scope() "
            f"вместо session_scope(): {statement.strip()[:120]}"
        )


@contextmanager
def foreign_keys_disabled(connection: Connection) -> Iterator[None]:
    """Выключить проверку ссылок на время изменения схемы (SQLite; иначе — ничего).

    Пересоздание таблицы (batch-миграция) проходит через удаление старой, а при
    включённой проверке удаление таблицы неявно удаляет все её строки — и действия
    внешних ключей на этом удалении срабатывают по-настоящему: дети уезжают каскадом,
    а миграция рапортует успех.

    Переключатель обязан стоять вне транзакции: внутри неё он молча не действует, без
    ошибки и предупреждения. Поэтому прагма идёт мимо SQLAlchemy — прямо в драйверное
    соединение, до того как начнётся транзакция миграции.
    """
    if connection.dialect.name != "sqlite":
        yield
        return
    if not _switch_foreign_keys(connection, enabled=False):
        raise RuntimeError(
            "sqlite: проверку ссылок не удалось выключить — переключатель не действует "
            "внутри открытой транзакции; выключай до первого оператора на соединении"
        )
    body_failed = False
    try:
        yield
        _raise_on_foreign_key_violations(connection)
    except BaseException:
        body_failed = True
        raise
    finally:
        # Вернуть проверку можно только вне транзакции, а alembic оставляет открытой ту,
        # в которой читал таблицу версий (заметно, когда накатывать нечего).
        _close_transaction(connection, rollback=body_failed)
        if not _switch_foreign_keys(connection, enabled=True):
            # Соединение с выключенной проверкой не должно вернуться в пул.
            _LOG.error("sqlite: проверка ссылок не восстановлена — соединение отбраковано")
            connection.invalidate()


def _close_transaction(connection: Connection, *, rollback: bool) -> None:
    if not connection.in_transaction():
        return
    connection.rollback() if rollback else connection.commit()


def _read(cursor, pragma: str):
    cursor.execute(f"PRAGMA {pragma}")
    return cursor.fetchone()[0]


def foreign_keys_enabled(connection: Connection) -> bool:
    """Действует ли проверка ссылок на этом соединении (читается у драйвера)."""
    cursor = _driver_cursor(connection)
    try:
        cursor.execute("PRAGMA foreign_keys")
        return bool(cursor.fetchone()[0])
    finally:
        cursor.close()


def _driver_cursor(connection: Connection):
    """Курсор драйвера — в обход транзакционного учёта SQLAlchemy."""
    return connection.connection.dbapi_connection.cursor()


def _switch_foreign_keys(connection: Connection, *, enabled: bool) -> bool:
    """Переключить проверку и убедиться, что переключение состоялось.

    Внутри открытой транзакции прагма — пустая операция без ошибки, поэтому
    единственный способ узнать результат — прочитать её обратно.
    """
    cursor = _driver_cursor(connection)
    try:
        cursor.execute(f"PRAGMA foreign_keys = {'ON' if enabled else 'OFF'}")
    finally:
        cursor.close()
    return foreign_keys_enabled(connection) is enabled


def _raise_on_foreign_key_violations(connection: Connection) -> None:
    cursor = _driver_cursor(connection)
    try:
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
    finally:
        cursor.close()
    if violations:
        raise RuntimeError(
            f"sqlite: миграции оставили нарушения ссылочной целостности ({len(violations)}): "
            f"{violations[:_VIOLATIONS_IN_MESSAGE]}"
        )


__all__ = [
    "WRITE_EXECUTION_OPTIONS",
    "configure_sqlite",
    "connection_pragmas",
    "foreign_keys_disabled",
    "foreign_keys_enabled",
]
