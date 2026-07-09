---
title: OpenRouter — баланс/лимиты ключа
date: 2026-07-06
description: "Read-эндпойнты баланса OpenRouter (GET /api/v1/key и /credits): лимит по ключу vs фактические кредиты аккаунта. Сверено живьём через упрощённый бенч-шлюз."
tags: [external-service, billing]
---

## Scope

Только **баланс** (для мониторинга коннекторов) — не инференс. Полный `OpenRouterProvider`
(chat completions, provider-routing, structured output, каталог моделей) из semaphore-core в
коннекторы не тянем. Сверено живьём: `dev/bench/core_connectors/openrouter/run_balance.py`
(упрощённый httpx-шлюз, ключ из ENV `OPENROUTER_API_KEY`). База `https://openrouter.ai/api/v1`,
auth `Authorization: Bearer <key>`.

## Findings

- **Два независимых показателя** (одно другое не отменяет):
  - **Лимит по ключу** — `GET /api/v1/key` → `data`: `usage` (израсходовано, all-time, USD),
    `limit` (потолок трат ключа, null=безлимит), `limit_remaining` (остаток под лимитом),
    `usage_daily`/`usage_weekly`/`usage_monthly`, `is_free_tier`, `label`. Пример: usage=5.16,
    limit=10, limit_remaining=4.84 → «использовано 5.16 / 10 USD».
  - **Кредиты аккаунта** — `GET /api/v1/credits` → `data`: `total_credits` (куплено),
    `total_usage` (весь расход). Баланс = `total_credits − total_usage`. ⚠ **Может быть
    отрицательным**: пример total_credits=5, total_usage=5.16 → −0.16 (usage включает
    free-tier/промо-кредиты сверх купленных).
- Всё в **USD** (float, не центы — в отличие от xAI management).
- Для мониторинга: `/key` `limit_remaining` — осязаемый «сколько ещё можно потратить»; `usage`/
  `limit` ложатся в форму «использовано / всего» с процентом. `/credits` — второй, аккаунтовый.

## Limits / quirks

- `limit`/`limit_remaining` = null, если у ключа нет лимита (безлимитный ключ) → «использовано из»
  не построить, останется только `usage` и/или `/credits`-баланс.
- Креды планируем держать в **ENV** на уровне модуля коннекторов (не runtime-настройки).

## References

- Docs: https://openrouter.ai/docs/api-reference/limits
- Живой бенч: `dev/bench/core_connectors/openrouter/run_balance.py` (+ `tmp/balance.json`)
- Полный провайдер (референс, НЕ тянем): `AGENTS/semaphore-core/src/modules/llm_providers/providers/openrouter.py`
