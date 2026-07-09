---
title: Balance DTO → list of metrics; OpenRouter balance bench
date: 2026-07-06
status: completed
description: "Переделать баланс коннектора в СПИСОК метрик (баланс, лимит ключа, кредиты — сосуществуют, выводим что доступно). Плюс упрощённый бенч-шлюз OpenRouter — проверить баланс живьём (полный провайдер не тянем)."
tags: [core_connectors, balance, dto, openrouter, bench]
---

## Task

«Переделаем DTO и вывод: у нас будут и лимиты по ключу, и фактический баланс — одно другое не отменяет, выводим что доступно.» Предыстория: пример `OpenRouterProvider` из semaphore-core слишком функциональный, чтобы тянуть в коннекторы; нужен только баланс. Просьба: на верстаке сделать упрощённый шлюз и проверить баланс.

## What was done

**OpenRouter — упрощённый бенч-шлюз (без инференса)**
- `dev/bench/core_connectors/openrouter/run_balance.py`: минимальный `OpenRouterGateway` (httpx+Bearer, только `key_info()`/`credits()`). Ключ из ENV `OPENROUTER_API_KEY` (для прогона взят из `.env` semaphore-core; в src OpenRouter будет с ENV-кредами на уровне модуля коннекторов).
- Сверено живьём: `GET /api/v1/key` → usage 5.16 / limit 10 / limit_remaining 4.84; `GET /api/v1/credits` → total_credits 5 − total_usage 5.16 = **−0.16** (может быть отрицательным). Всё USD. → research `AGENTS/research/openrouter/INDEX.md`.

**DTO баланса → список метрик** (`services/dto.py`)
- `ConnectorBalance` теперь `service`/`name` + **`metrics: list[BalanceMetric]`** + `error` (было: плоские `amount`/`credits_*`).
- `BalanceMetric` — одна метрика: `label` + денежная (`amount`+`currency`) ИЛИ «использовано из всего» (`used`/`total`/`used_percent`+`unit`). Фабрики `money(label, amount)` / `usage(label, used, total, unit)` (сама считает %). Убрана `ConnectorBalance.from_credits`.
- Гейтвеи: Tavily/Firecrawl → одна метрика «Кредиты» (used/total из plan); xAI management → метрика «Баланс» (money, инверсия знака). Пустой ответ → `metrics=[]`.

**Фронт**
- `api.ts` — `BalanceMetric` + `ConnectorBalance.metrics`. Компонент `ConnectorBalance.vue` теперь на **массиве метрик**: на метрику строка (`label` + значение деньги/«used / total unit» + `% использовано` + бар всегда); `error`/`placeholder` — отдельные строки. Единая вёрстка карточек (3-строчное описание, бар всегда) сохранена. Локаль: `balance.unit.<code>` вместо старых ключей.
- Тесты переписаны на метрики (8, pure); бенч `run_balances.py` печатает метрики.

## Result

- Live `GET /internal/connectors`: tavily/firecrawl → метрика «Кредиты» (17/1000 1.7%, 102/1000 10.2%), xai → «Баланс» $6.02.
- `--module=core_connectors` 8 / `vue-tsc` чист; `web/dist` пересобран. Research OpenRouter + INDEX добавлены.
- **Не делалось (следующий шаг):** перенос OpenRouter в src как коннектор (ENV-креды, `ServiceGateway`-подкласс, `balance()` → метрики «Лимит ключа» + «Баланс»); вторая ось Firecrawl (tokens) как отдельная метрика.
