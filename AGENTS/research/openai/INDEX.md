---
title: OpenAI — баланс/расход через API
date: 2026-07-06
description: "У OpenAI нет надёжного API остатка (credit_grants — только браузерный session-токен, протухает). Программно доступен РАСХОД через Admin Costs API. Эндпойнты, auth, схемы. Сверено ЖИВЬЁМ (Admin-ключ)."
tags: [external-service, billing]
---

## Scope

Можно ли получить баланс/расход OpenAI программно (для коннектора-мониторинга). По офиц.
докам developers.openai.com + cookbook; живьём НЕ гоняли (нет Admin-ключа).

## Findings

- **Надёжного остатка баланса через API НЕТ.** `GET /v1/dashboard/billing/credit_grants` отдаёт
  остаток (`total_granted`/`total_used`/`total_available`), но работает **только с браузерным
  session-токеном** (Okta/Auth0), НЕ с `sk-…`/admin, протухает за дни → для автоматизации не годится.
- **Есть РАСХОД — Admin Costs API** (нужен **Admin-ключ** `sk-admin-…`; header
  `Authorization: Bearer <admin_key>`):
  - `GET https://api.openai.com/v1/organization/costs`
    - Params: `start_time` (Unix-секунды, обяз., inclusive), `end_time` (Unix, exclusive),
      `bucket_width="1d"` (только), `group_by[]` (`project_id`/`line_item`/`api_key_id`),
      `limit` (1..180, default 7), `page` (курсор), `project_ids`/`api_key_ids`.
    - Ответ (сверено живьём): `{object:"page", data:[{object:"bucket", start_time, end_time,
      results:[{object:"organization.costs.result", amount:{value, currency}, quantity, line_item,
      project_id, project_name, api_key_id, user_id, user_email, organization_id, organization_name}]}],
      has_more, next_page}`. 30-дн окно = 31 дневной бакет, одна страница (`has_more=false`).
    - ⚠ **`amount.value` — СТРОКА высокой точности** (напр. `"2.714130800000000000000000000"`),
      **не** float (в примере доков — float, в реале — строка!) → приводить `float(value)`. `currency="usd"`,
      **в ДОЛЛАРАХ** (в отличие от Anthropic — там центы-строка). **Расход = Σ float(results[].amount.value)**.
    - ⚠ Обычный/проектный ключ (`sk-…`/`sk-proj-…`) → **403**; нужен именно **Admin `sk-admin-…`**.
      Плохо заскоупленный admin-ключ иногда → 404. Сверено: `sk-admin-…` → 200, «Расход 30д» = $3.51.
  - Токены (не деньги) — `GET /v1/organization/usage/completions` (и др. `usage/*`).

## Limits / quirks

- Нет надёжного остатка → для коннектора максимум «Расход за N дней» (метрика-деньги без total), не баланс.
- Admin-ключ обязателен (обычный `sk-…` к costs доступа не даёт).
- `credit_grants` — session-only, для прод-мониторинга непригоден.

## References

- Costs API ref: https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs
- Usage/Cost cookbook: https://developers.openai.com/cookbook/examples/completions_usage_api
