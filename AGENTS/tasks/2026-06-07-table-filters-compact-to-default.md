---
title: Table pages — filter fields compact → default size
date: 2026-06-07
status: completed
description: "Across all list/table pages (except conversation_insights/processed), bump filter input controls (VSelect/VAutocomplete/VTextField/VDateInput/search) from density=compact to default — they were 28px after the density-axis fix and felt cramped. Tables, toggles, dialog forms, lists left untouched."
tags: [frontend, design-system, vuetify]
---

## Task

«…/conversations, /conversations/participants и другие страницы с таблицами, кроме
/conversation-insights/processed — пройдись и поправь размер с компактного на обычный.»

Follow-up to [[2026-06-07-ds-field-size-density-axis]]: now that `density` genuinely
drives height (default 36 / comfortable 32 / compact 28px), the compact filter fields on
list pages read as too small.

Clarified via AskUserQuestion:
- **What** = only filter INPUT controls (VSelect/VAutocomplete/VTextField/VDateInput/
  VSelectSearch/search). NOT the data table, NOT VBtnToggle, NOT dialog form fields,
  NOT VAlert/VList/VCheckbox.
- **Scope** = all table/list pages EXCEPT `conversation_insights/processed`.

## Approach

Remove `density="compact"` (→ implicit `default`) from filter-row input controls only.
Dialog edit-form fields keep their compact density (not filters). Tables keep
`comfortable`.

## Pages (filter rows)

- conversations: ConversationsFilters.vue, views/ParticipantsView.vue
- intercom: ConversationsView, ContactsView
- twenty: OpportunitiesView, PeopleView, CompaniesView
- mail_sync: ThreadsView, MessagesView, FiltersView
- core_geo: LanguagesView, TimezonesView, ContinentsView, CountriesView
- core_monitoring: TasksView, TaskRunsView
- agents: ModelsView, McpView (filter row only)
- administration: UsersView
- team: PeopleView (filter row only — dialog fields stay)
- conversation_insights reports: CountriesReportView, VolumeReportView
- conversation_insights: TaggingRulesView (filter row only — dialog stays)

## Done — 20 files

Removed `density="compact"` (→ default 36px) from filter input controls on:
conversations Filters + ParticipantsView; intercom Conversations + Contacts; twenty
Opportunities + People + Companies; mail_sync Threads + Messages; core_geo Languages +
Timezones + Continents + Countries; core_monitoring Tasks + TaskRuns; agents Models +
Mcp (search); ci reports Countries + Volume; ci TaggingRules (search — targeted edit, its
dialog fields left compact).

Verified in browser: `/conversations` filter fields all 36px (were 28px).

## Intentionally skipped (not filter input fields)

- **Dialog form fields**: mail_sync/FiltersView, administration/UsersView,
  team/PeopleView, conversation_insights/TaggingRulesView (dialog part), agents
  *EditDialog components, SetPasswordDialog — compact form fields inside dialogs, not filters.
- **VBtnToggle** (view/status switches): core_monitoring/TasksView, agents/AgentSessionsView,
  ProcessedConversationsView — user excluded toggles.
- **VList / VSwitch / VAlert**: twenty *View VList, agents/McpView VSwitch, intercom/AdminsView
  VList, TaskRunsView VAlert — not input fields.
- **conversation_insights/processed** — excluded per request.
- team/PeopleView filter row uses `comfortable`, not compact — out of "compact→default" scope.

