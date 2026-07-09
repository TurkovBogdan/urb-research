# web_search — поиск в вебе + сохранение найденных страниц

Модуль (`src/modules/web_search/`) — зона ответственности «внешний веб»: запрос к
движкам (поиск / скрейп / агентский синтез), сохранение выдачи и контента найденных
страниц (приведение к единому **markdown** — побочный эффект). «Модуль сырых данных»
центральной памяти по ресёрчу (дизайн — `AGENTS/obsidian/general.canvas` +
`sources-engines.md`).

Модуль различает **две независимые функции** внешнего веба, у каждой свой провайдер
(и своя настройка по умолчанию): **движок поиска** (`SearchEngine`) отдаёт ссылки, а
**движок получения контента** (`FetchEngine`) по ссылкам скачивает markdown. Один
провайдер может уметь обе (Tavily, Firecrawl); Grok (xAI) умеет только поиск, а
`daemon-web-scrapper` (`web_scrapper`, локальный демон) — только контент.

Исполнение **синхронное**: `services/searcher.search` за один `await` создаёт запрос,
зовёт движок поиска, сохраняет выдачу и дотягивает контент найденных страниц сервисом
контента, финализирует запрос и возвращает его. Ни очереди, ни планировщик-задач, ни
ретраев.

## Таблицы (тройка ядра)

`запрос (NL) → выдача (URL) → контент страницы`:

- **`web_search_query`** — прогоны поиска (NL). PK — **голый 22-hex код** `code`,
  **случайный** (`crud.query.query_code()` через `hashing.random_hash()`: у прогона нет
  естественного ключа дедупа — повторный запрос = новый прогон). `search_engine` (снимок
  активного движка поиска) + `fetch_engine` (снимок движка контента) — **две колонки
  `String(64)`**, обе NOT NULL, фиксируют кто искал и кто тянул контент,
  `query`, `params` (JSON — все параметры запроса: `max_results` + include/exclude_domains,
  time_range), `error` (nullable, код/имя типа исключения при сбое), `status` — машина `pending` (создан, работа ещё
  не началась) → `processing` (идёт синхронный прогон: вызов движка + фетч страниц) → `done`
  (выполнен, в т.ч. если результатов не нашлось — статуса `empty` больше нет) / `error`
  (движок упал — терминально, без повторов).
- **`web_search_page`** — контент страницы, **дедуп по url**: PK — **голый 22-hex код**
  `code`, **детерминированный** (`crud.page.page_code()` = `text_hash(normalize_url)`) — сам
  код и есть ключ дедупа по url. Хранится только
  обработанный `content` (markdown) + `content_hash` (raw не храним).
  `title` (String(512), nullable — заголовок документа, **свойство самой страницы**, не
  запроса: берётся из выдачи поиска при создании, дедуп не перетирает — первый нашедший движок
  задаёт). `status` — та же машина `pending` (создана, контент ещё не получен) → `processing`
  (идёт получение контента) → `done` (контент получен) / `error` (фетч упал — терминально, без
  повторов); `domain`, `error` (nullable, код ошибки), `fetched_at`.
- **`web_search_query_result`** — результаты запроса (внутренняя связка запрос↔документ,
  нейронка на неё не ссылается → оставляет суррогатный int `id`): FK `query_code` →
  `web_search_query.code`, `page_code` → `web_search_page.code` (страница создаётся
  в `pending`). `rank`, `score`, `summary` (Text — краткое содержание страницы в контексте запроса,
  общее для всех движков: Tavily `content`, Firecrawl `description`, xAI — поле строгого вывода),
  `meta` (JSON — остаточные **контекстные** поля движка: reason/favicon/…; заголовок сюда НЕ
  кладём — он на `web_search_page.title`). `QueryResultView` отдаёт заголовок как `page_title`
  (из джойна со страницей). `unique (query_code, page_code)`; индекс `ix_web_search_query_result_query_code`.

Миграции `migrations/versions/wsm_001..003` на **портируемых типах** (`json_value()`/`timestamp()` из
`core/database/types.py` — через `.with_variant` дают `JSONB`/`TIMESTAMP` на PG и `JSON`/`DateTime` на SQLite),
поэтому `migrate upgrade` идёт **и на SQLite, и на Postgres** (core-миграции `com_*` переведены так же).
Модели = миграции (парити на PG: heavy `compare_metadata`). Схему строит **Alembic** (`migrate upgrade` /
lifespan): файловая dev-sqlite и Postgres — через миграции; `create_all` только для in-memory тестов
(`config.sqlite_in_memory`). Правка схемы = правка миграции + пересборка dev (drop файла + `migrate upgrade`).
Идентификаторы: PK — **голый 22-hex хеш** (`String(25)` со слаком, `core/utils/hashing.py`); числового
`id` на этих двух таблицах **больше нет**. `web_search_query.code` = `random_hash()` (случайный — дедупа
у прогона нет), `web_search_page.code` = `text_hash(normalize_url)` (детерминированный — дедуп по url на
уровне БД). **web_search коды не типизирует** — его модели/API отдают голый хеш. Читаемый тип-префикс
`type@hash` (`SEARCH@`/`PAGE@`) надевает только модуль **research**, когда ссылается на эти коды (кодек —
`src/modules/research/codes.py`); web_search его не импортирует (направление зависимости research→web_search).
`web_search_query_result` оставляет суррогатный int `id`, FK — на коды (`query_code`/`page_code`, `String(25)`). Нормализация
url минимальная: **всегда https** (`normalize_url` в `crud/page.py`). JSON-колонки — `json_value()` (на SQLite = `JSON`/TEXT).

## Состав

- `module.py` — `WebSearchModule`: `name`, `settings_schema`, `migrations_dir`, `internal_router`+`internal_router_prefix` (`/web-search`). Ни `config_cls` (токены переехали в `core_connectors`), ни `configure()`/`register_tasks` — исполнение синхронное, планировщик-задач не нужен.
- `migrations/versions/` — `wsm_001_query` → `wsm_002_page` → `wsm_003_result` (портируемые типы; идут и на SQLite, и на PG).
- `settings.py` — `SCHEMA`: **два `ChoiceField` под две роли** — `search_engine` (tavily|firecrawl|xai, default tavily — движок, отдающий ссылки) + `fetch_engine` (tavily|firecrawl, default tavily — движок, скачивающий контент; Grok не умеет), плюс три `IntField` в порядке схемы: `default_pages` (default 10 — «Страниц на поисковый запрос», `max_results` по умолчанию) + `max_concurrent_searches` (default 3, min 1 / max 50 — «Максимум параллельных поисковых запросов», троттлинг-гейт per-engine, см. `services/searcher.py`) + `fetch_concurrency` (default 5 — «Максимум параллельных запросов получения контента», семафор фетча внутри одного поиска). Читается через `get_module_store("web_search")`; хелперы `search_engine()`/`fetch_engine()`/`default_pages()`/`max_concurrent_searches()`/`fetch_concurrency()` (падают на default из констант модуля). Термин — **engine**, не provider (по всей цепочке: настройки/колонки/реестры/`Searcher`). **Токены провайдеров тут НЕ живут** — они в `core_connectors`. Поля рендерятся на `/core/settings` из схемы по `kind` (лейбл — с бэка).
- `constants.py` — статусы таблиц (общий источник для моделей, миграций, CRUD), **два набора по ролям**, одинаковая машина `pending → processing → done | error`: `SEARCH_STATUS_*` (прогон поиска, `web_search_query`) и `FETCH_STATUS_*` (получение контента, `web_search_page`); `SEARCH_STATUSES`/`FETCH_STATUSES` + `sql_in` для CheckConstraint.
- `models/` — `query.py` / `page.py` / `query_result.py` (схема — миграции `wsm_001..003`; `create_all` только в in-memory тестах). **Каждый файл держит ORM + свой read-DTO рядом** (колокация, отдельного `dto.py` нет): `query.py` — `WebSearchQuery` + `QueryRow`/`QueryDetail`; `page.py` — `WebSearchPage` + `PageRow`/`PageDetail`; `query_result.py` — `WebSearchQueryResult` + `QueryResultView`. Даты сериализуются ядровым `DatetimeUTCStr` (`core/utils/date.py` — SQL-формат `"yyyy-MM-dd HH:mm:ss"`, без `T`; фронт-парсер `web/src/shared/utils/date.ts` = Luxon `fromSQL`, pydantic-дефолт ISO даёт `—`). Конверт списка — ядровый `core.api.Paged` (`core/api/pagination.py`).
- `crud/` — по файлу на сущность (`query`/`page`/`query_result`). Ретраев/очереди нет:
  `query` (ключ — `code`): `query_create` (строка в `pending`, `code=query_code()`, снимает `search_engine`+`fetch_engine`, параметры → `params`), `query_get(code)`, `query_mark_processing(code)` (→`processing`), `query_finish(code)` (→`done`, даже без результатов), `query_mark_error(code, *, error=…)` (статус `error` + код в колонку `error`), read-листинги `query_list`/`query_count` (фильтры текст/статус/`search_engine` + `sort_by`/`sort_dir` + offset/limit; `sort_by` — **белый список** `QUERY_SORT_COLUMNS` = `created_at`/`finished_at`/`status`/`search_engine`/`fetch_engine`/`query`, неизвестный ключ → дефолт `created_at`; `code` — стабильный тайбрейк в ту же сторону). **Троттлинг:** `query_processing_count(search_engine, *, since)` (свежие `processing` по движку — счётчик занятых слотов; старее `since` не считаются) + `query_expire_stale(search_engine, *, before)` (добить залипшие `processing` `updated_at < before` → `error="stale"`, reaper без планировщика). Индекс `ix_web_search_query_engine_status` (`search_engine`,`status`) под этот счёт.
  `page`: `page_upsert` (создать в `pending` или вернуть по дедуп-коду), `pages_mark_processing(codes)` (батч →`processing` перед фетчем), `page_set_content` (→`done`), `page_set_error(code, *, error=…)` (статус `error` + код в колонку `error`), read-листинги `page_list`/`page_count` (фильтры текст/статус/домен + `sort_by`/`sort_dir`; `sort_by` — белый список `PAGE_SORT_COLUMNS` = `created_at`/`fetched_at`/`status`/`domain`/`url`, неизвестный → `created_at`).
  `query_result`: `result_add(query_code=…, page_code=…)`, `results_for_query(query_code)`, `results_with_page_for_query(query_code)` (результаты запроса джойном со страницей).
- `api.py` — `APIRouter` (зона `internal`, `/web-search`). **Просмотр:** `GET /queries` (пагинация+фильтры; фильтр по движку `search_engine`; `sort_by`/`sort_dir`), `GET /queries/{code}` (запрос + выдача с полями страниц), `GET /pages` (фильтры + `sort_by`/`sort_dir`), `GET /pages/{code}` (страница с контентом). `sort_by` дефолт `created_at`, `sort_dir` `desc`. **Запуск:** `POST /queries` (тело `CreateQueryBody`: `query` непустой ≤2000, `search_engine?`/`fetch_engine?`/`max_results?` 1..50 — None→дефолт настроек) → `Searcher.submit(...)` → **202** + `pending`-`QueryRow` сразу (**fire-and-forget**, клиент не ждёт; неизвестный движок → `KeyError`→**400**). `GET /engines` → `EnginesInfo` (`search`/`fetch` = доступные коды из `Searcher.*_engines()` + `search_default`/`fetch_default` из настроек) — для селектов формы.
  Guard не нужен — internal в чистом ядре `allow_all`. Фронт-фича: `web/src/features/web_search/` (две страницы
  список→детальная: Запросы / Страницы) — таблицы `VDataTable` с серверной **сортировкой по клику на заголовок** (`must-sort`, `@update:sort-by` → стор `sortBy`/`sortDir` → `sort_by`/`sort_dir`), пагинация `TablePaginationBar`, даты в две строки (`fmtDateTime` + относительная `fmtRelative`); **создание запроса** — кнопка → `VDialog` с формой (текст + выбор движков поиска/контента из `GET /engines` с преселектом дефолта + число страниц 1..50), submit → `POST /queries` → обновление списка (запрос виден `pending`→`processing`→`done` по «Обновить»); nav-группа «Веб-поиск», `MarkdownRenderer` для контента.
- `services/searcher.py` — **статический класс-фасад `Searcher`**. Публичные: `search_engines()`/`fetch_engines()` (коды доступных движков по ролям = `<registry>.available_codes()`) + **два способа запуска**: `search(query, *, search_engine=None, fetch_engine=None, max_results=None, include/exclude_domains, time_range) -> WebSearchQuery` (**блокирующий** — прогон целиком, вернуть завершённый; MCP/скрипты/тесты) и `submit(...)` (**fire-and-forget** — создать `pending`, запустить прогон фоном через `asyncio.create_task`+`_schedule`/`_BACKGROUND_TASKS`, вернуть `pending`-строку сразу; HTTP-создание). Оба делят `_prepare` (резолв движков → `KeyError` на неизвестном коде ДО создания строки → `query_create`) + `_run` (гейт слота → `processing` → поиск → сохранение → фетч → `done`). Приватные геттеры дефолта `_default_search_engine()`/`_default_fetch_engine()` (= `settings.search_engine()`/`fetch_engine()`) подставляются, когда движок не задан. Реестры импортированы как `search_engine_registry`/`fetch_engine_registry` (чтобы не путать с одноимёнными публичными методами).
  `search` строит `SearchRequest` (`max_results` не задан → настройка `default_pages`), резолвит движки (`<registry>.get(<param> or <default>)`), `query_create` снимком обоих
  (строка `pending`; `to_params()` кладёт в `params` все параметры запроса, включая `max_results`). Затем в
  **том же вызове**: `_acquire_search_slot(engine.code)` (**троттлинг, режим задержки**: ждёт, пока свежих `processing`
  по движку `< max_concurrent_searches`, опрашивая с джиттером `random.uniform(0.5,1.5)s`; перед подсчётом
  `query_expire_stale` добивает залипшие `processing` старше `_PROCESSING_STALE_TTL`=15мин → `error`, иначе краш держал бы
  слот вечно; лимит **мягкий** — счётчик в БД общий для всех процессов; фетч ограничен транзитивно ≈ слоты × `fetch_concurrency`) →
  `query_mark_processing` (→`processing`) → `engine.search(request)` (только ссылки, без контента) →
  `_store_results` (создаёт `pending`-страницы) → `_fetch_pages(fetcher, pending)` (батчами по `fetcher.pages_per_request`:
  `pages_mark_processing` → фетч → `done`/`error`; параллельно под семафором `fetch_concurrency`) →
  `query_finish` (→`done`, даже если результатов не нашлось) → возвращает завершённый запрос.
  Движок поиска отключён в `core_connectors` (`engine.available()` False) → запрос сразу `error` (`error="search_engine_disabled"`, до сети).
  Сбой движка → `query_mark_error` (запрос `error`, **исключение не пробрасывается**); сбой фетча батча → эти страницы `error`.
  Приватные шаги того же файла (не отдельный «сервис»): `_store_results(query_code, results) -> list[WebSearchPage]`
  (page на url → result; возвращает новые `pending`-страницы под до-фетч, уже `done` по дедупу переиспользуются; статус
  запроса не трогает — движки поиска контент не отдают) и `_fetch_pages` (фетч контента). `services/save.py` удалён —
  склейка была фейковым «сервисом» (возврат `pending` = оркестрационный сигнал для `_fetch_pages`, дом — оркестратор).
- `providers/` — **пакеты по провайдерам**; **две независимые роли (общего предка нет) + два реестра-класса**
  (оркестрацию держит `services/searcher.py`):
  - `base.SearchEngine(ABC)` — движок поиска: `code` + `enabled_field` (= `ENABLED_FIELD` коннектора) + `available()` (`service_enabled` — коннектор можно выключить) + `search(request)->list[{url,rank?,score?,summary?,title?,meta?}]` (**только ссылки, без контента**; `summary` = краткое содержание страницы в контексте запроса — Tavily `content`, Firecrawl `description`, xAI поле строгого вывода — пишется в колонку `web_search_query_result.summary`; `title` = заголовок документа — верхний ключ, пишется в `web_search_page.title` (свойство страницы, не запроса); `meta` = остаточные контекстные поля движка вроде reason).
  - `base.FetchEngine(ABC)` — движок контента: те же `code`/`enabled_field`/`available()` (**продублированы**, не унаследованы) + ClassVar `pages_per_request` (Tavily **20**, Firecrawl **1**, web_scrapper **10**) + `fetch_pages(urls)->{url: md|None}` (батч до `pages_per_request` url).
  - Провайдер, умеющий обе роли (Tavily, Firecrawl), реализует оба класса и регистрируется в **обоих** реестрах; `client.py` = адаптер над коннектором `core_connectors` (задаёт `enabled_field = XxxGateway.ENABLED_FIELD`).
  - `web_scrapper/` — пакет `WebScrapperEngine` (**только контент**): адаптер над коннектором `core_connectors.services.web_scrapper` (локальный демон `daemon-web-scrapper`, порт 19020). `fetch_pages(urls)` → батч `POST /api/1.0/scrap-batch`, маппит каждый `results[].url → content` (markdown; неуспешный outcome или отсутствующий url → `None`). `pages_per_request=10` (= `SCRAPE_BATCH_CONCURRENCY` демона). Поиска нет — в реестр поиска не регистрируется.
  - `registry` — **два реестра-класса** `SearchEngineRegistry`/`FetchEngineRegistry` (`EngineRegistry[E]` generic) + синглтоны `search_engines`/`fetch_engines`: `register(engine)`, `get(code)`, `codes()` (все) / `available_codes()` + `is_available(code)` (**учёт доступности через `core_connectors`** — только включённые коннекторы).
  - `__init__.py` пакета провайдера регистрирует инстанс: Tavily/Firecrawl → `search_engines.register`+`fetch_engines.register`; xai → только `search_engines.register`; web_scrapper → только `fetch_engines.register`.
  - `xai/` — пакет `XaiSearchEngine` (**только поиск**): у Grok нет search-эндпойнта — поиск = **агентский** инференс `core_connectors` xAI `responses()` с server-side инструментом `web_search` + **строгий structured output**. Модель сама ранжирует и возвращает JSON-массив `links` (url/title/summary/reason/relevance; `LINKS_SCHEMA` + `json_schema_text`, strict) под инструкцией `AGENT_INSTRUCTION` (роль ресёрчера, «не выдумывай URL», дать `summary` = краткое содержание). Но URL печатает сама модель → **grounding-фильтр**: оставляем только `links[].url`, реально встреченные в `web_search_call.action.sources` (по нормализованному url `_norm_url`), остальное отбрасываем (защита от галлюцинаций); затем обрезаем до `max_results`. Маппинг в контракт: `relevance→score`, `rank` по порядку, `summary→summary`, `title→title` (→ `web_search_page.title`), `meta={reason}`. Строгий JSON не распарсился → пустая выдача. Контент Grok не умеет — в реестр контента не регистрируется. (эталон логики — бенч `dev/bench/core_connectors/xai/verify_relevant_links.py`)
  - `request.SearchRequest` (provider-agnostic; `from_stored` восстанавливает из строки БД). Пакеты: `tavily/`, `firecrawl/`, `xai/`.
- Коды/нормализация url живут **по месту использования** (файла `normalize.py` больше нет): `normalize_url` (https), `page_code` (голый url-хеш, детерминированный) и `domain_of` — в `crud/page.py`; `query_code` (голый `random_hash`, случайный) — в `crud/query.py`. Верстаки: `dev/bench/web_search/{tavily,firecrawl,xai}/` (xai гоняет провайдер-адаптер `XaiSearchEngine`, т.к. raw search-эндпойнта нет; сырой коннектор — `dev/bench/core_connectors/xai/`).

## Настройки (runtime, БД)

Провайдеры (по одному на роль) и параллелизм фетча — **runtime-настройки** (`core_modules_settings`, применяются горячо,
без рестарта), НЕ ENV. Правятся на **`/core/settings`** (карточка web_search):

Порядок полей на `/core/settings` = порядок в `SCHEMA` (лейбл — с бэка):

| Ключ настройки | Тип | Лейбл / назначение |
|---|---|---|
| `search_engine` | choice (tavily\|firecrawl\|xai, default tavily) | «Поисковый движок» — активный движок поиска (отдаёт ссылки) |
| `fetch_engine` | choice (tavily\|firecrawl\|web_scrapper, default tavily) | «Сервис получения контента» — активный движок фетча (Grok не умеет; web_scrapper — локальный демон daemon-web-scrapper) |
| `default_pages` | int (1..50, default 10) | «Страниц на поисковый запрос» — `max_results` по умолчанию (если не задан явно) |
| `max_concurrent_searches` | int (1..50, default 3) | «Максимум параллельных поисковых запросов» — троттлинг-гейт (per-provider) |
| `fetch_concurrency` | int (1..50, default 5) | «Максимум параллельных запросов получения контента» — семафор фетча **внутри одного поиска** |

**Токены провайдеров тут НЕ живут** — они в модуле `core_connectors` (коннекторы владеют кредами);
`client.py` каждого провайдера берёт ключ через `core_connectors.settings.service_api_key`.
Токенов в `.env`/`core_setup` тоже нет — там остались только серверные ключи (БД/сервер/воркер).

## Открыто (обсуждается)

- Внешний **триггер** `search` (MCP-инструмент / HTTP-роут) — пока вызывается программно (read-API уже есть, write — нет).
- Переиспользование запроса (дедупа нет — повторный запрос = новый вызов провайдера); TTL на повторный фетч `done`-страниц.
- Векторный слой (recall) поверх `web_search_page.content`.

Каталог движков (что отдаёт каждый, A/B/C, цены): `AGENTS/obsidian/sources-engines.md`.
