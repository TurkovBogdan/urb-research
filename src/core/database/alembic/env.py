"""Alembic environment configured programmatically by AlembicRunner.

Метаданные моделей собираются автоматически: каждый модуль импортирует свои
``models`` в ``__init__.py`` (что регистрирует их в ``Base.metadata``).
К моменту запуска миграций модули уже импортированы из ``apps/<name>/server.py``.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.core.database.runtime import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = config.attributes.get("connection")
    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        ).connect()
        own_connection = True
    else:
        own_connection = False
    try:
        context.configure(connection=connectable, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    finally:
        if own_connection:
            connectable.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
