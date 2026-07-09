"""core_setup: построчный редактор .env — сохранение комментариев + правка на месте."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.modules.core_setup import env_file
from src.modules.core_setup.keys import FIELDS


def _fake_config(**over) -> SimpleNamespace:
    """Config-стенд: атрибут на каждый ENV-ключ формы (ключ в нижнем регистре)."""
    values = {f.key.lower(): "" for f in FIELDS}
    values.update(over)
    return SimpleNamespace(**values)


@pytest.mark.pure
def test_write_preserves_comments_replaces_in_place_appends_missing(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text(
        "# header comment\n"
        "DB_PROVIDER=postgres\n"
        "# inline doc for port\n"
        "DB_PORT=5432\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(env_file, "env_path", lambda: path)

    env_file.write_values({"DB_PROVIDER": "sqlite", "NEW_KEY": "x"})

    text = path.read_text(encoding="utf-8")
    assert "# header comment" in text  # комментарии сохранены
    assert "# inline doc for port" in text
    assert "DB_PROVIDER=sqlite" in text  # заменено на месте
    assert "DB_PORT=5432" in text  # нетронутый ключ
    assert "NEW_KEY=x" in text  # дописан в конец
    # порядок исходных строк не нарушен
    assert text.index("DB_PROVIDER") < text.index("DB_PORT") < text.index("NEW_KEY")


@pytest.mark.pure
def test_read_values_picks_only_requested_keys(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("DB_PROVIDER=sqlite\nDB_PORT=5432\nIGNORED=1\n", encoding="utf-8")
    monkeypatch.setattr(env_file, "env_path", lambda: path)

    assert env_file.read_values(["DB_PROVIDER", "DB_PORT"]) == {
        "DB_PROVIDER": "sqlite",
        "DB_PORT": "5432",
    }


@pytest.mark.pure
def test_seed_creates_env_with_defaults_when_absent(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    monkeypatch.setattr(env_file, "env_path", lambda: path)
    config = _fake_config(
        db_provider="sqlite", db_ssl=True, db_port=5432,
        server_port=13410, server_vite_port=None, worker_enabled=False,
    )

    created = env_file.seed_defaults_if_absent(config)

    assert created is True
    values = env_file.read_values([f.key for f in FIELDS])
    assert set(values) == {f.key for f in FIELDS}  # все поля формы записаны
    assert values["DB_PROVIDER"] == "sqlite"
    assert values["DB_SSL"] == "true"  # bool → true/false
    assert values["SERVER_PORT"] == "13410"  # int → строка
    assert values["SERVER_VITE_PORT"] == ""  # None → пусто
    assert values["WORKER_ENABLED"] == "false"


@pytest.mark.pure
def test_seed_is_noop_when_env_exists(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("DB_PROVIDER=postgres\n", encoding="utf-8")
    monkeypatch.setattr(env_file, "env_path", lambda: path)

    created = env_file.seed_defaults_if_absent(_fake_config(db_provider="sqlite"))

    assert created is False
    assert path.read_text(encoding="utf-8") == "DB_PROVIDER=postgres\n"  # не тронут
