---
title: Multi-root views blank on revisit under Transition+KeepAlive
date: 2026-06-04
status: completed
description: "Twenty/opportunities (and other dialog-bearing views) rendered a blank content zone on the second in-app visit. Cause: multi-root view template can't be animated by <Transition mode=out-in>. Fixed by making each view single-root."
tags: [frontend, routing, vuetify]
---

## Task

User: open http://localhost:12100/twenty/opportunities, click around the menu — content does not load on the second visit. Figure out why, then fix.

## Context

`App.vue` wraps the content zone as `RouterView → <Transition mode="out-in" appear> → <KeepAlive> → <component :is="Component" class="h-100">`. `<Transition>` can only animate a component with a **single root element**.

The three Twenty views (`OpportunitiesView`, `CompaniesView`, `PeopleView`), plus `intercom/AdminsView` and `conversation_insights/TaggingRulesView`, had a **multi-root** template: `<PageLayout>` followed by sibling `<VDialog>`s at the root. That is a fragment, not an element.

- First visit works because `appear` mounts the component directly (no out-in leave/enter handoff).
- On the second visit (in-app nav back), `mode="out-in"` runs leave→enter over the KeepAlive-cached fragment; the handoff breaks for a fragment root → outgoing page removed, incoming never shown → blank white content zone.
- Console smoking gun: `[Vue warn]: Component inside <Transition> renders non-element root node that cannot be animated. at <OpportunitiesView class="h-100"> at <KeepAlive> at <Transition mode="out-in">`.
- F5 (full reload) hid the bug because it re-enters via `appear`.

Single-root views (`ConversationsView`, `ParticipantsView`, `ProcessedConversationsView`, `ConversationView`, `ReportsIndexView`) were unaffected — confirming the correlation.

## What was done

Made each affected view single-root by moving the sibling `<VDialog>`s (and custom dialog wrappers, which are `<VDialog>`-rooted → also teleport) **inside** `<PageLayout>`. DOM position is irrelevant since they teleport to `<body>`. Minimal diff: relocated the closing `</PageLayout>` tag past the dialogs in each file.

First pass (Twenty bug report):
- `web/src/features/twenty/views/{Opportunities,Companies,People}View.vue`
- `web/src/features/intercom/views/AdminsView.vue`
- `web/src/features/conversation_insights/views/TaggingRulesView.vue`

Second pass — full codebase sweep for the same pattern (user: "проверь остальные модули"). Audited every `*.vue` for elements after the root `</PageLayout>`; fixed the remaining 9:
- `web/src/features/administration/views/UsersView.vue` (+2 dialogs)
- `web/src/features/agents/views/AgentsView.vue` (+`AgentConfigEditDialog`)
- `web/src/features/agents/views/McpView.vue` (+`McpEditDialog` +dialog)
- `web/src/features/intercom/views/ContactsView.vue` (+dialog)
- `web/src/features/intercom/views/ConversationsView.vue` (+dialog)
- `web/src/features/mail_sync/views/FiltersView.vue` (+3 dialogs)
- `web/src/features/mail_sync/views/MessagesView.vue` (+2 dialogs)
- `web/src/features/team/views/PeopleView.vue` (+3 dialogs)
- `web/src/views/design-system/feedback/DialogsView.vue` (+5 dialogs)

False positive ruled out: `views/design-system/basics/LayoutView.vue` flagged only because its `<script>` holds a code-sample string containing literal `<template>…</template>` — its real template is single-root.

No tests (FE template-only). `vue-tsc --noEmit` clean. Verified in-browser: Сделки→Компании→Сделки (twenty) and Агенты→Члены команды (team) both render on the 2nd visit; Vue warning gone.

## Result

14 routed views converted to single-root (5 first pass + 9 sweep); the `<Transition mode="out-in"> + <KeepAlive>` blank-on-revisit bug is resolved codebase-wide. No multi-root routed views remain.
