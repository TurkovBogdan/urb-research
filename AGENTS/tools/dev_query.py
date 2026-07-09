"""Ad-hoc SQL против dev-базы. Запускается обёрткой dev-query.sh через `uv run`.

Бэкенд выбирается по `DB_PROVIDER` из `.env` — как в приложении: `sqlite` (dev по
умолчанию) идёт в файл `runtime/<APP_ENV>/app.sqlite3` (либо `DB_PATH`), `postgres`
— в `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`. Раньше скрипт всегда ходил в
Postgres и расходился с приложением на sqlite. Запрос берётся из аргументов
командной строки или, если их нет, из stdin.

Только для dev. Запрос выполняется как есть — никаких ограничений на DDL/DML тут
нет, ответственность на вызывающем.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
from pathlib import Path

import asyncpg

# Корень проекта передаёт обёртка dev-query.sh (AGENTS — симлинк, поэтому
# __file__.resolve() увёл бы нас в цель симлинка). Фолбэк — текущая директория.
_ROOT = Path(os.environ.get("DEV_QUERY_ROOT", Path.cwd()))
_ENV = _ROOT / ".env"
_MAX_CELL = 80  # обрезаем длинные значения, чтобы таблица оставалась читаемой


def _load_env() -> dict[str, str]:
    """Распарсить нужные ключи из .env (KEY=VALUE, без экспорта/кавычек): DB_* + APP_ENV."""
    if not _ENV.exists():
        sys.exit(f"error: .env not found at {_ENV}")
    out: dict[str, str] = {}
    for raw in _ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("DB_") or key == "APP_ENV":
            out[key] = val.strip()
    return out


def _sqlite_path(env: dict[str, str]) -> Path:
    """Файл dev-SQLite — тем же путём, что и приложение (src/core/config.py::_sqlite_path):
    ``DB_PATH`` если задан, иначе ``runtime/<APP_ENV>/app.sqlite3`` (профиль по умолчанию dev)."""
    db_path = env.get("DB_PATH", "")
    if db_path:
        candidate = Path(db_path)
        return candidate if candidate.is_absolute() else _ROOT / candidate
    profile = os.environ.get("APP_ENV") or env.get("APP_ENV") or "dev"
    return _ROOT / "runtime" / profile / "app.sqlite3"


def _is_read_query(sql: str) -> bool:
    return sql.lstrip().lower().startswith(
        ("select", "with", "show", "explain", "table", "pragma")
    )


def _fmt_cell(val: object) -> str:
    s = "NULL" if val is None else str(val)
    s = s.replace("\n", "\\n").replace("\t", "\\t")
    return s if len(s) <= _MAX_CELL else s[: _MAX_CELL - 1] + "…"


def _print_table(rows: list) -> None:
    if not rows:
        print("(0 rows)")
        return
    cols = list(rows[0].keys())
    cells = [[_fmt_cell(r[c]) for c in cols] for r in rows]
    widths = [max(len(cols[i]), *(len(row[i]) for row in cells)) for i in range(len(cols))]
    sep = "-+-".join("-" * w for w in widths)
    print(" | ".join(c.ljust(widths[i]) for i, c in enumerate(cols)))
    print(sep)
    for row in cells:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(cols))))
    print(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")


async def _run_postgres(sql: str, env: dict[str, str]) -> None:
    missing = [k for k in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD") if not env.get(k)]
    if missing:
        sys.exit(f"error: missing in .env: {', '.join(missing)}")
    conn = await asyncpg.connect(
        host=env["DB_HOST"],
        port=int(env.get("DB_PORT", "5432")),
        user=env["DB_USER"],
        password=env["DB_PASSWORD"],
        database=env["DB_NAME"],
    )
    try:
        if _is_read_query(sql):
            _print_table(await conn.fetch(sql))
        else:
            print(await conn.execute(sql))
    finally:
        await conn.close()


def _run_sqlite(sql: str, path: Path) -> None:
    if not path.exists():
        sys.exit(f"error: sqlite db not found at {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        if _is_read_query(sql):
            _print_table(cursor.fetchall())
        else:
            conn.commit()
            print(f"OK ({cursor.rowcount} rows)")
    finally:
        conn.close()


def main() -> None:
    sql = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not sql:
        sys.exit("usage: dev-query.sh \"SELECT ...\"   |   echo \"SELECT ...\" | dev-query.sh")
    env = _load_env()
    if env.get("DB_PROVIDER", "postgres") == "sqlite":
        _run_sqlite(sql, _sqlite_path(env))
    else:
        asyncio.run(_run_postgres(sql, env))


if __name__ == "__main__":
    main()
