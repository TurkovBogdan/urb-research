# core/loggers

Каналы логирования: имя → инстанс `CoreLoggerProtocol`. Один канал — один файл `logs/<channel>.log`, никакой иерархии и пропагации в `logging.root`.

Слеш в имени канала превращается в подпапку: `tasks/hh_vacancy_scrapper` → `logs/tasks/hh_vacancy_scrapper.log`. Подпапки создаются автоматически.

## Публичный API

```python
from src.core.loggers import get_logger, set_logger_factory, LoggerStore
```

| Имя | Назначение |
|-----|------------|
| `get_logger(*channels)` | прокси канала(ов); без аргументов — `core`; ≥2 канала — tee |
| `set_logger_factory(factory)` | bootstrap: установить фабрику `(channel) -> CoreLoggerProtocol` |
| `LoggerStore` | реестр каналов; `set/get/reset` для тестов |

Всё остальное (`CoreLogger`, `_LoggerProxy`, `CoreLoggerProtocol`, `LoggerFactory`) — внутренние детали; импортируются из своих модулей напрямую, когда действительно нужны (bootstrap, тесты).

## Каналы по конвенции

Каналы — плоские строки, которые уже используются в коде. Новых не вводим без необходимости:

| Канал | Где появляется | Файл |
|-------|----------------|------|
| `core` | дефолт `get_logger()` | `logs/core.log` |
| `tasks` | `core/scheduler/{runner,ticker,context}.py` | `logs/tasks.log` |
| `page_scraper` | `modules/page_scraper/services/*` | `logs/page_scraper.log` |
| `hh.browser` | `modules/headhunter/browser/*` (включая `scenarios.py`) | `logs/hh.browser.log` |
| `hh.scraper` | `modules/headhunter/scraper/scraper.py` | `logs/hh.scraper.log` |
| `integrated_browser` | `modules/integrated_browser/*` | `logs/integrated_browser.log` |

## Использование

### Один канал

```python
# src/modules/page_scraper/services/gateway.py
from src.core.loggers import get_logger

_LOG = get_logger("page_scraper")  # → logs/page_scraper.log

def set_server(...) -> None:
    _LOG.info("server set: %s", endpoint)
```

### Канал `core` по умолчанию

```python
_LOG = get_logger()
_LOG.info("startup")               # пишет в logs/core.log
```

### Подканал (подпапка)

Слеш в имени → файл лежит во вложенной директории. Удобно, когда у одного «домена» (например, `tasks`) много дочерних потоков и хочется группировать их физически:

```python
_LOG = get_logger("tasks/hh_vacancy_scrapper")  # → logs/tasks/hh_vacancy_scrapper.log
```

Это просто нейминг файла; для `LoggerStore` канал остаётся плоской строкой `"tasks/hh_vacancy_scrapper"` — отдельным от `"tasks"`. Если нужно писать **и** в общий, **и** в подканал — используй tee.

### Несколько каналов сразу (fan-out)

```python
_LOG = get_logger("hh.browser", "tasks")
_LOG.info("vacancy %s scraped in %.2fs", vacancy_id, elapsed)
# → строка попадёт в logs/hh.browser.log И в logs/tasks.log
```

Tee хорошо ложится и на подканалы — детальный лог в отдельный файл, общий поток — в `tasks`:

```python
_LOG = get_logger("tasks", "tasks/hh_vacancy_scrapper")
# → logs/tasks.log + logs/tasks/hh_vacancy_scrapper.log
```

`set_level` на tee применяется ко всем каналам сразу.

## Устройство

| Файл | Роль |
|------|------|
| `logger_protocol.py` | `CoreLoggerProtocol` — минимальный контракт |
| `logger_store.py` | `LoggerStore` (кеш «канал → инстанс») + `set_logger_factory` |
| `core_logger.py` | `CoreLogger` — пишет в `logs/<channel>.log`, без stdout |
| `logger_proxy.py` | `_LoggerProxy` / `_TeeProxy`, `get_logger` |
| `__init__.py` | публичный фасад: `get_logger`, `set_logger_factory`, `LoggerStore` |

## Прокси: зачем он

`get_logger(...)` возвращает **прокси**, не инстанс. Каждый вызов лога резолвится через `LoggerStore.get(channel)`:

```python
# В модуле, на импорте — bootstrap ещё не отработал.
_LOG = get_logger("tasks")   # это _LoggerProxy("tasks")

# Позже apps/app/server.py выполнит set_logger_factory(...).
# Следующий вызов уже резолвится через новую фабрику:
_LOG.info("task started")    # пишет в logs/tasks.log с правильным уровнем
```

Если бы `get_logger` отдавал сам инстанс, модули с `_LOG = get_logger(...)` на уровне модуля захватили бы дефолтный логгер, созданный до bootstrap, и игнорировали бы конфигурацию. `_TeeProxy` устроен так же: на каждый вызов резолвит каждый канал через store.

## Bootstrap

`src/apps/app/server.py`:

```python
from src.core.app_path import AppPath, ensure_dirs
from src.core.loggers import set_logger_factory
from src.core.loggers.core_logger import CoreLogger

def _bootstrap_logger(settings: Settings) -> None:
    paths = AppPath.from_root()
    ensure_dirs(paths)

    def factory(channel: str) -> CoreLogger:
        return CoreLogger(
            logs_dir=paths.logs,
            file_name=channel,
            level=settings.log_level,
        )

    set_logger_factory(factory)
```

`set_logger_factory` сбрасывает уже закэшированные каналы — ранние импорты до bootstrap не залипают со старой конфигурацией.

## Тесты

`tests/core/test_loggers.py` сбрасывает store autouse-фикстурой:

```python
@pytest.fixture(autouse=True)
def _reset_store():
    LoggerStore.reset()
    yield
    LoggerStore.reset()
```

Подмена канала на конкретный инстанс:

```python
custom = CoreLogger(logs_dir=tmp_path, file_name="custom")
LoggerStore.set(custom, "tasks")   # фиксирует инстанс в канале "tasks"
LoggerStore.set(None, "tasks")     # снимает override
```

Подмена фабрики целиком:

```python
set_logger_factory(lambda ch: CoreLogger(
    logs_dir=tmp_path, file_name=ch, level=logging.DEBUG
))
get_logger("hh.browser", "tasks").info("fanout")

for ch in ("hh.browser", "tasks"):
    for h in logging.getLogger(f"core.{ch}").handlers:
        h.flush()
    assert "fanout" in (tmp_path / f"{ch}.log").read_text()
```
