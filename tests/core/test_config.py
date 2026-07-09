"""Config + get_config."""

from __future__ import annotations

import ssl

import certifi
import pytest

from src.core.config import Config, get_config


@pytest.mark.pure
def test_loads_from_dotenv():
    s = Config()
    assert s.db_host
    assert s.db_name
    assert s.db_user
    assert s.db_password
    assert s.db_port == 5432


@pytest.mark.pure
def test_database_url_format():
    s = _config(db_provider="postgres", db_host="db.example", db_name="appdb", db_port=6000)
    url = s.database_url
    assert url.startswith("postgresql+asyncpg://")
    assert s.db_host in url
    assert s.db_name in url
    assert str(s.db_port) in url


@pytest.mark.pure
def test_defaults(monkeypatch):
    """Дефолты конструктора без .env и без env-переменных."""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("SERVER_VITE_PORT", raising=False)
    s = Config(
        _env_file=None,
        db_host="x", db_name="x", db_user="x", db_password="x",
        db_ssl=False,
    )
    assert s.app_env == "prod"
    assert s.app_log_level == "INFO"
    assert s.db_echo is False
    # По умолчанию server_vite_port не задан → CORS-origins пусты (прод).
    assert s.cors_origins == []
    assert s.server_processes == 1


def _config(**over) -> Config:
    base = dict(
        _env_file=None,
        db_host="x", db_name="x", db_user="x", db_password="x",
        db_ssl=False,
    )
    return Config(**{**base, **over})


@pytest.mark.pure
def test_cors_origins_from_vite_port():
    """server_vite_port задан → dev-CORS origins для localhost/127.0.0.1."""
    s = _config(server_vite_port=12100)
    assert s.cors_origins == [
        "http://localhost:12100",
        "http://127.0.0.1:12100",
    ]


@pytest.mark.pure
def test_empty_optional_int_in_dotenv_uses_default(tmp_path, monkeypatch):
    """Пустое значение в .env (`SERVER_VITE_PORT=`) = «не задано» → дефолт, а не ""
    (иначе валидация `int | None` падает). Насиженный .env содержит такие пустые поля."""
    monkeypatch.delenv("SERVER_VITE_PORT", raising=False)
    env = tmp_path / ".env"
    env.write_text("DB_PROVIDER=sqlite\nSERVER_VITE_PORT=\n", encoding="utf-8")
    assert Config(_env_file=str(env)).server_vite_port is None


@pytest.mark.pure
def test_worker_modules_set_parsing():
    """worker_modules (CSV) → frozenset; пусто → None."""
    assert _config(worker_modules="").worker_modules_set is None
    assert _config(worker_modules=" a , b ,a").worker_modules_set == frozenset({"a", "b"})


@pytest.mark.pure
def test_connect_args_no_ssl():
    """db_ssl=False → есть таймаут, нет ssl."""
    args = _config(db_ssl=False, db_connect_timeout=7).db_connect_args
    assert args["timeout"] == 7
    assert "ssl" not in args


@pytest.mark.pure
def test_connect_args_verify_full():
    """db_ssl=True + валидный CA → SSLContext в режиме verify-full."""
    args = _config(db_ssl=True, db_cert=certifi.where()).db_connect_args
    ctx = args["ssl"]
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.check_hostname is True
    assert ctx.verify_mode == ssl.CERT_REQUIRED


@pytest.mark.pure
def test_ssl_requires_cert():
    """db_ssl=True без cert → ValueError на старте (проверка только для postgres)."""
    with pytest.raises(ValueError, match="DB_CERT required"):
        _config(db_provider="postgres", db_ssl=True, db_cert=None)


@pytest.mark.pure
def test_connect_args_mtls_loads_client_chain(monkeypatch):
    """db_client_cert/key → клиентский сертификат подгружается в контекст."""
    seen = {}
    monkeypatch.setattr(
        ssl.SSLContext, "load_cert_chain",
        lambda self, certfile, keyfile: seen.update(certfile=certfile, keyfile=keyfile),
    )
    args = _config(
        db_ssl=True, db_cert=certifi.where(),
        db_client_cert="/abs/client.crt", db_client_key="/abs/client.key",
    ).db_connect_args
    assert isinstance(args["ssl"], ssl.SSLContext)
    assert seen == {"certfile": "/abs/client.crt", "keyfile": "/abs/client.key"}


@pytest.mark.pure
def test_client_cert_requires_pair():
    """Клиентский cert без key (или наоборот) → ValueError."""
    with pytest.raises(ValueError, match="must be set together"):
        _config(db_ssl=True, db_cert=certifi.where(), db_client_cert="/abs/client.crt")


@pytest.mark.pure
def test_cert_relative_path_resolves_from_app_root(tmp_path, monkeypatch):
    """Относительный db_cert резолвится от корня приложения."""
    import src.core.config as config_mod
    from pathlib import Path

    (tmp_path / "ca.pem").write_bytes(Path(certifi.where()).read_bytes())
    monkeypatch.setattr(config_mod, "_app_root", lambda: tmp_path)
    args = _config(db_ssl=True, db_cert="ca.pem").db_connect_args
    assert isinstance(args["ssl"], ssl.SSLContext)


@pytest.mark.pure
def test_get_config_cached():
    a = get_config()
    b = get_config()
    assert a is b


@pytest.mark.pure
def test_extra_env_vars_ignored(monkeypatch):
    """Лишние переменные в окружении не должны ломать инициализацию."""
    monkeypatch.setenv("RANDOM_UNKNOWN_VAR", "foo")
    s = Config()
    assert s.db_host  # инициализировался
