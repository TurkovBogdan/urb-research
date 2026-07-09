"""core_setup: построчный редактор .env — сохранение комментариев + правка на месте."""

from __future__ import annotations

import pytest

from src.modules.core_setup import env_file


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
