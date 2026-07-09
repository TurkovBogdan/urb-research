---
title: Restore default field density inside modals
date: 2026-06-07
status: completed
description: "Follow-up to the density-axis fix — now that Vuetify density genuinely drives field height, walk every modal/dialog and bump reduced-size input fields and dropdowns back to default (normal) size. Verify each change in the browser."
tags: [web, frontend, design-system, dialogs]
---

## Task

> Мы заставили правильно работать density. Теперь нужно пройтись по модалкам в web/src, посмотреть где используются поля ввода и выпадающие списки уменьшенного размера и сделать их обычными — именно в модалках. Каждое изменение проверять в браузере.

## Context

Sibling of [[2026-06-07-ds-field-size-density-axis]] — density now actually changes field height (default 36 / comfortable 32 / compact 28px). Many dialogs were written with `density="compact"/"comfortable"` on text fields and selects back when density was visually a no-op; now they render visibly cramped. Inside roomy modals we want full-size (default density) inputs.

Scope = input fields and dropdowns (`VTextField`, `VSelect`, `VAutocomplete`, `VCombobox`, `VTextarea`, `VNumberInput`, `VDateInput`) inside `VDialog`s. Leave checkboxes / buttons / btn-toggles / alerts / lists as-is unless they read cramped.

Dialogs in scope (from grep of density inside VDialog blocks):
- features/agents/components/ModelEditDialog.vue
- features/agents/components/AgentConfigEditDialog.vue
- features/agents/components/McpEditDialog.vue
- features/user-profile/components/CreateTokenDialog.vue
- features/administration/components/SetPasswordDialog.vue
- features/administration/views/UsersView.vue (add dialog)
- features/conversation_insights/views/TaggingRulesView.vue (edit dialog)
- features/team/views/PeopleView.vue (member + contacts dialogs)
- features/mail_sync/views/FiltersView.vue (filter dialog)

## What was done

Removed `density="compact" / "comfortable"` from every **input field / dropdown** (`VTextField`, `VTextarea`, `VSelect`, `VCombobox`, `VNumberInput`, `ProviderModelSelect`) inside dialogs, letting them fall back to the global default density (36px). Left checkboxes, switches, `VBtn`/`VBtnToggle`, `VAlert`, and `VList` density untouched (those aren't input fields). Edited files:
- `features/agents/components/ModelEditDialog.vue` — combobox + 5 number/text fields (kept the Supports/Input/Output checkbox matrix compact).
- `features/agents/components/AgentConfigEditDialog.vue` — cron/runs/concurrency/temperature/max-tokens/budget fields; `ProviderModelSelect` set to `density="default"` explicitly (its `withDefaults` defaults to `compact`, so just dropping the prop would NOT restore full size — that was the one trap).
- `features/agents/components/McpEditDialog.vue` — code/name/description + config textarea.
- `features/conversation_insights/views/TaggingRulesView.vue` — name/category/code + description/prompt textareas.
- `features/user-profile/components/CreateTokenDialog.vue` — token name field.
- `features/administration/components/SetPasswordDialog.vue` — new/confirm password fields.
- `features/administration/views/UsersView.vue` — add-user email/password.
- `features/team/views/PeopleView.vue` — member dialog (name/role/notes) + contacts editor inline rows (kind select / value / label).
- `features/mail_sync/views/FiltersView.vue` — type select + code/name/rule.

Out of scope (checked, no reduced inputs inside the modal): twenty import/detail dialogs (VList only), GeoIndexView sync, McpInfoPanel, TokensCard confirm. `McpView` / `ModelsView` reduced fields are page **filter bars**, not modals — left alone.

No tests (pure FE styling). `vue-tsc --noEmit` clean (exit 0).

## Problems

`ProviderModelSelect` defaults `density` to `compact` via `withDefaults`, so removing the prop at the call site keeps it compact — had to pass `density="default"` explicitly there.

## Result

All nine dialogs above now render full-size (default density) inputs. Each verified in the browser (open dialog → confirm field height). Files changed: the nine `.vue` files listed under *What was done*.
