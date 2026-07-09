# Верстак Tavily

Отработка методов Tavily на реальном API: что умеет, как запускается поиск, в каком виде
возвращает данные. Ключ — Tavily API-ключ из runtime-настроек `core_connectors`.
Сырые ответы складываются в `tmp/` (идея «получить раз — гонять локально»).

## Запуск

```bash
uv run python -m dev.bench.web_search.tavily.run_search       # базовый поиск
uv run python -m dev.bench.web_search.tavily.run_search_raw   # поиск + полный контент + answer
uv run python -m dev.bench.web_search.tavily.run_extract      # контент по списку URL
uv run python -m dev.bench.web_search.tavily.run_map          # обнаружение URL сайта (beta)
```

Аутентификация — заголовок `Authorization: Bearer <key>` (подтверждено живыми вызовами).
База: `https://api.tavily.com`, эндпоинты `POST /search`, `/extract`, `/map`, `/crawl` (beta, не гоняли).

## Что вернулось (проверено)

### `POST /search`
- **Запрос:** `query`, `search_depth` (`basic`=1кр / `advanced`=2кр; есть `fast`/`ultra-fast`),
  `max_results` (0–20), `topic` (`general`/`news`), `include_answer`, `include_raw_content`
  (`false` / `"markdown"` / `"text"`), `include_domains`/`exclude_domains`, `time_range`.
- **Ответ (top-level):** `query`, `results[]`, `answer`, `follow_up_questions`, `images`,
  `response_time`, `request_id`. `answer`/`follow_up_questions`/`images` = `null`, если не запрошены.
- **Поле результата:** `title`, `url`, `content` (короткий сниппет, ~1 КБ), `score` (релевантность 0–1),
  `raw_content` (`null`, **если не задан** `include_raw_content`). `published_date` — только при `topic=news`.
- Базовый прогон: 5 результатов, `response_time≈0.85s`, `content` 138–1111 символов.

### `POST /search` + `include_raw_content="markdown"`
- Тот же поиск, но `raw_content` каждого результата = **полное тело страницы в markdown** (~18–20 КБ).
- `include_answer=true` → `answer` = LLM-синтез по выдаче (короткий абзац).
- **Вывод:** Tavily умеет отдать поиск + тело + ответ за один вызов (наш бакет **A+B**, чуть **C**).

### `POST /extract`
- **Запрос:** `urls` (строка/массив), `format` (`markdown`/`text`), `extract_depth` (`basic`/`advanced`).
- **Ответ:** `results[]` (`url`, `raw_content` ~21 КБ, `title`, `images`), `failed_results[]`,
  `response_time`, `request_id`. У результата **нет** `content`/`score` (в отличие от search).
- Путь «доскрейпа» указателей (bucket B) и цитат (bucket C) → тело `document`.

### `POST /map` (beta)
- **Запрос:** `url`, `max_depth`, `max_breadth`, `limit`. **Ответ:** `base_url`, `results[]` =
  плоский список URL (контента нет), `response_time`, `request_id`.
- Прогон по `docs.tavily.com`: 20 URL, **включая внешние** (x.com, discord, github) — не только домен.

## Гранёные углы

- `content` (сниппет ~1 КБ) ≠ `raw_content` (полная страница ~20 КБ): сниппет для ранжирования,
  raw — для хранения/чанкинга. `raw_content` не добавляет кредитов.
- Формы результата у `search` и `extract` **разные** (у extract нет `content`/`score`).
- `map` тянет и off-domain ссылки — фильтровать на нашей стороне.
- Поля `usage`/кредиты приходят только при `include_usage=true` (в этих прогонах не запрашивали).
- Цены (из доков, не мерили): search 1/2 кр, extract 1 кр/5URL (basic) / 2 кр (advanced), map 1 кр/10 стр.

Полный каталог движков и классификация A/B/C — `AGENTS/obsidian/sources-engines.md`.
Артефакты прогонов — `tmp/{search,search_raw,extract,map}.json`.
