"""Loggers: каналы, LoggerStore, прокси, CoreLogger, tee."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.core.loggers import LoggerStore, get_logger, set_logger_factory
from src.core.loggers.core_logger import CoreLogger


@pytest.fixture(autouse=True)
def _reset_store():
    LoggerStore.reset()
    yield
    LoggerStore.reset()


def _flush(*channels: str) -> None:
    for ch in channels:
        name = "core." + ch.replace("/", ".")
        for h in logging.getLogger(name).handlers:
            h.flush()


# ── Store: получение и фабрика ───────────────────────────────────────────────

@pytest.mark.pure
def test_store_lazy_default_creates_core_logger():
    """Без фабрики ``get`` лениво создаёт CoreLogger."""
    log = LoggerStore.get("core")
    assert isinstance(log, CoreLogger)


@pytest.mark.pure
def test_store_caches_per_channel(tmp_path: Path):
    set_logger_factory(lambda ch: CoreLogger(logs_dir=tmp_path, file_name=ch))
    a1 = LoggerStore.get("alpha")
    a2 = LoggerStore.get("alpha")
    b = LoggerStore.get("beta")
    assert a1 is a2
    assert a1 is not b


@pytest.mark.pure
def test_store_factory_called_with_channel_name(tmp_path: Path):
    captured: list[str] = []

    def factory(channel: str) -> CoreLogger:
        captured.append(channel)
        return CoreLogger(logs_dir=tmp_path, file_name=channel)

    set_logger_factory(factory)
    LoggerStore.get("scheduler")
    LoggerStore.get("hh.browser")
    assert captured == ["scheduler", "hh.browser"]


@pytest.mark.pure
def test_set_factory_clears_cached_channels(tmp_path: Path):
    """После ``set_factory`` все ранее закэшированные каналы пересоздаются."""
    first = LoggerStore.get("core")
    set_logger_factory(lambda ch: CoreLogger(logs_dir=tmp_path, file_name=ch))
    second = LoggerStore.get("core")
    assert first is not second


@pytest.mark.pure
def test_store_set_overrides_channel(tmp_path: Path):
    custom = CoreLogger(logs_dir=tmp_path, file_name="custom")
    LoggerStore.set(custom, "scheduler")
    assert LoggerStore.get("scheduler") is custom


@pytest.mark.pure
def test_store_set_none_clears_override(tmp_path: Path):
    set_logger_factory(lambda ch: CoreLogger(logs_dir=tmp_path, file_name=ch))
    custom = CoreLogger(logs_dir=tmp_path, file_name="x")
    LoggerStore.set(custom, "alpha")
    LoggerStore.set(None, "alpha")
    # снова через фабрику
    log = LoggerStore.get("alpha")
    assert log is not custom


@pytest.mark.pure
def test_store_set_default_channel_is_core(tmp_path: Path):
    custom = CoreLogger(logs_dir=tmp_path, file_name="z")
    LoggerStore.set(custom)
    assert LoggerStore.get() is custom
    assert LoggerStore.get("core") is custom


# ── get_logger: прокси и канал по умолчанию ──────────────────────────────────

@pytest.mark.pure
def test_get_logger_default_channel_is_core(tmp_path: Path):
    """``get_logger()`` без аргумента — канал ``core``."""
    factory_calls: list[str] = []

    def factory(channel: str) -> CoreLogger:
        factory_calls.append(channel)
        return CoreLogger(logs_dir=tmp_path, file_name=channel)

    set_logger_factory(factory)
    log = get_logger()
    log.info("hi")
    assert factory_calls == ["core"]


@pytest.mark.pure
def test_get_logger_returns_proxy_resolving_through_store(tmp_path: Path):
    """Прокси канала видит замену логгера, выполненную ПОСЛЕ его создания."""
    set_logger_factory(lambda ch: CoreLogger(logs_dir=tmp_path, file_name=ch))
    proxy = get_logger("scheduler")
    proxy.info("first")

    replacement = CoreLogger(
        logs_dir=tmp_path, file_name="scheduler-replacement", level=logging.DEBUG
    )
    LoggerStore.set(replacement, "scheduler")
    proxy.info("second")

    _flush("scheduler-replacement")
    assert "second" in (tmp_path / "scheduler-replacement.log").read_text()


@pytest.mark.pure
def test_get_logger_writes_to_per_channel_file(tmp_path: Path):
    set_logger_factory(lambda ch: CoreLogger(
        logs_dir=tmp_path, file_name=ch, level=logging.DEBUG
    ))

    sched = get_logger("scheduler")
    page = get_logger("page_scraper")
    sched.info("tick")
    page.info("probe")

    _flush("scheduler", "page_scraper")

    assert "tick" in (tmp_path / "scheduler.log").read_text()
    assert "probe" in (tmp_path / "page_scraper.log").read_text()
    assert "tick" not in (tmp_path / "page_scraper.log").read_text()


# ── CoreLogger: конкретная реализация ────────────────────────────────────────

@pytest.mark.pure
def test_core_logger_writes_file(tmp_path: Path):
    log = CoreLogger(logs_dir=tmp_path, file_name="sys", level=logging.DEBUG)
    log.info("alpha")
    log.warning("beta")
    log.error("gamma")
    _flush("sys")
    text = (tmp_path / "sys.log").read_text()
    assert "alpha" in text
    assert "beta" in text
    assert "gamma" in text


@pytest.mark.pure
def test_core_logger_creates_dir(tmp_path: Path):
    nested = tmp_path / "deep" / "logs"
    CoreLogger(logs_dir=nested, file_name="x")
    assert nested.is_dir()


@pytest.mark.pure
def test_core_logger_nested_channel_creates_subdir(tmp_path: Path):
    """`file_name` со слешем → подпапка под logs_dir."""
    log = CoreLogger(
        logs_dir=tmp_path, file_name="tasks/data_import", level=logging.DEBUG
    )
    log.info("nested")
    log_path = tmp_path / "tasks" / "data_import.log"
    _flush("tasks/data_import")
    assert log_path.is_file()
    assert "nested" in log_path.read_text()


@pytest.mark.pure
def test_get_logger_nested_channel(tmp_path: Path):
    """get_logger('tasks/...') пишет в logs/tasks/<name>.log через фабрику."""
    set_logger_factory(lambda ch: CoreLogger(
        logs_dir=tmp_path, file_name=ch, level=logging.DEBUG
    ))
    log = get_logger("tasks/data_scrapper")
    log.info("scraped")
    _flush("tasks/data_scrapper")
    assert "scraped" in (tmp_path / "tasks" / "data_scrapper.log").read_text()


@pytest.mark.pure
def test_core_logger_set_level(tmp_path: Path):
    log = CoreLogger(logs_dir=tmp_path, file_name="lvl", level=logging.INFO)
    log.debug("hidden")
    log.set_level(logging.DEBUG)
    log.debug("visible")
    _flush("lvl")
    text = (tmp_path / "lvl.log").read_text()
    assert "hidden" not in text
    assert "visible" in text


# ── Tee: фан-аут в несколько каналов ─────────────────────────────────────────

@pytest.mark.pure
def test_tee_writes_to_all_channels(tmp_path: Path):
    set_logger_factory(lambda ch: CoreLogger(
        logs_dir=tmp_path, file_name=ch, level=logging.DEBUG
    ))
    log = get_logger("hh.browser", "tasks")
    log.info("fanout")
    _flush("hh.browser", "tasks")
    assert "fanout" in (tmp_path / "hh.browser.log").read_text()
    assert "fanout" in (tmp_path / "tasks.log").read_text()


@pytest.mark.pure
def test_tee_dispatches_each_level(tmp_path: Path):
    set_logger_factory(lambda ch: CoreLogger(
        logs_dir=tmp_path, file_name=ch, level=logging.DEBUG
    ))
    log = get_logger("a", "b")
    log.debug("d-msg")
    log.info("i-msg")
    log.warning("w-msg")
    log.error("e-msg")
    _flush("a", "b")
    for name in ("a", "b"):
        text = (tmp_path / f"{name}.log").read_text()
        assert "d-msg" in text
        assert "i-msg" in text
        assert "w-msg" in text
        assert "e-msg" in text


@pytest.mark.pure
def test_tee_resolves_through_store_after_replacement(tmp_path: Path):
    """Tee видит замену канала, выполненную после создания прокси."""
    set_logger_factory(lambda ch: CoreLogger(
        logs_dir=tmp_path, file_name=ch, level=logging.DEBUG
    ))
    log = get_logger("alpha", "beta")
    log.info("before")

    replacement = CoreLogger(
        logs_dir=tmp_path, file_name="alpha-new", level=logging.DEBUG
    )
    LoggerStore.set(replacement, "alpha")
    log.info("after")

    _flush("alpha", "beta", "alpha-new")
    assert "before" in (tmp_path / "alpha.log").read_text()
    assert "after" not in (tmp_path / "alpha.log").read_text()
    assert "after" in (tmp_path / "alpha-new.log").read_text()
    # beta получает оба сообщения
    beta_text = (tmp_path / "beta.log").read_text()
    assert "before" in beta_text
    assert "after" in beta_text


@pytest.mark.pure
def test_tee_set_level_applies_to_all_channels(tmp_path: Path):
    set_logger_factory(lambda ch: CoreLogger(
        logs_dir=tmp_path, file_name=ch, level=logging.INFO
    ))
    log = get_logger("x", "y")
    log.debug("hidden")
    log.set_level(logging.DEBUG)
    log.debug("visible")
    _flush("x", "y")
    for name in ("x", "y"):
        text = (tmp_path / f"{name}.log").read_text()
        assert "hidden" not in text
        assert "visible" in text


@pytest.mark.pure
def test_get_logger_single_channel_returns_plain_proxy():
    """Один канал — обычный прокси, не tee (без накладных расходов на цикл)."""
    from src.core.loggers.logger_proxy import _LoggerProxy, _TeeProxy

    log = get_logger("solo")
    assert isinstance(log, _LoggerProxy)
    assert not isinstance(log, _TeeProxy)


@pytest.mark.pure
def test_get_logger_no_args_is_core_proxy():
    from src.core.loggers.logger_proxy import _LoggerProxy

    log = get_logger()
    assert isinstance(log, _LoggerProxy)


# ── _TeeStream: stream interface ─────────────────────────────────────────────

class _FakeStream:
    def __init__(self) -> None:
        self.buf = ""
        self._fd = 42

    def write(self, text: str) -> int:
        self.buf += text
        return len(text)

    def flush(self) -> None:
        pass

    def fileno(self) -> int:
        return self._fd


@pytest.mark.pure
def test_tee_stream_write(tmp_path: Path):
    from src.core.loggers.global_log import _TeeStream

    original = _FakeStream()
    tee = _TeeStream(original, tmp_path / "out.log")
    tee.write("hello\n")
    assert "hello" in original.buf
    assert "hello" in (tmp_path / "out.log").read_text()


@pytest.mark.pure
def test_tee_stream_fileno(tmp_path: Path):
    from src.core.loggers.global_log import _TeeStream

    original = _FakeStream()
    tee = _TeeStream(original, tmp_path / "out.log")
    assert tee.fileno() == 42


@pytest.mark.pure
def test_tee_stream_flush(tmp_path: Path):
    from src.core.loggers.global_log import _TeeStream

    original = _FakeStream()
    tee = _TeeStream(original, tmp_path / "out.log")
    tee.flush()


@pytest.mark.pure
def test_tee_stream_isatty(tmp_path: Path):
    from src.core.loggers.global_log import _TeeStream

    tee = _TeeStream(_FakeStream(), tmp_path / "out.log")
    assert tee.isatty() is False
