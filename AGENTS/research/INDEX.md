# research — index

Research artifacts for external services and technologies: API documentation, behavior, limits.

## Rules

- Log results of researching an external service or technology into `AGENTS/research/<topic>/`.
- Create `INDEX.md` inside the subfolder from `AGENTS/research/TEMPLATE.md` and add an entry below.
- Do not duplicate into memory — research stores raw data and details, memory stores final decisions made for the project.

## Inventory

- [tavily/](tavily/INDEX.md) — Tavily API: методы (search/extract/map/crawl), формат ответов, лимиты. Проверено живыми вызовами через верстак `dev/bench/web_content/tavily`.
- [xai/](xai/INDEX.md) — xAI (Grok) поиск контента: Agent Tools API на `/v1/responses` (web_search/x_search/code_execution/collections_search), multi-agent deep research, цитаты (только URL), модели/цены, снятие legacy Live Search. По докам, живьём не гоняли.
- [openrouter/](openrouter/INDEX.md) — OpenRouter баланс/лимиты ключа: `GET /api/v1/key` (usage/limit/limit_remaining) vs `GET /api/v1/credits` (total_credits−total_usage, может быть отрицательным). USD. Сверено живьём (упрощённый бенч-шлюз, только баланс).
- [anthropic/](anthropic/INDEX.md) — Claude: **остатка баланса через API НЕТ** (404, только console). Есть РАСХОД — Admin API `GET /v1/organizations/cost_report` (нужен Admin-ключ; ⚠ `amount` — строка в ЦЕНТАХ). По докам.
- [openai/](openai/INDEX.md) — OpenAI: надёжного остатка через API НЕТ (`credit_grants` — session-only). Есть РАСХОД — Admin `GET /v1/organization/costs` (нужен `sk-admin-…`; `amount.value` в долларах). По докам.
