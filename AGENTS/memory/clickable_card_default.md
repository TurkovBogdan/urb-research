---
name: clickable_card_default
description: Project-wide clickable card default = VCard link + global .v-card--link override; ripple off; bespoke card CSS migrated
metadata: 
  node_type: memory
  type: project
  originSessionId: c64ceba8-177b-45c5-9248-ec09ada7e0ba
---

Кликабельная карточка в проекте — это `<VCard>`, а НЕ самописный `<button>`/`<article>`. Дефолтный стиль задан глобально, страницы на него опираются (не дублируют hover/focus).

**Где живёт дефолт:**
- `web/src/styles/main.scss` — после блока `.v-card` идёт override для `.v-card--link, .v-card--hover`: гасит Vuetify-overlay (`.v-card__overlay { opacity:0 }`), держит плоско (обнуляет `::before/::after` тени), `text-decoration: none` в базе и в `:hover` (карточка с `:to` = `<a>` → иначе ловит глобальный `a:hover { text-decoration: underline }` из main.scss:150 и подчёркивает весь текст; `.v-card--link:hover` (0,2,0) бьёт `a:hover` (0,1,1) без !important), на `:hover` `border-color: var(--accent)`, на `:focus-visible` — кольцо `0 0 0 2px var(--accent-soft)`. Базовые surface/border-soft/radius/`box-shadow:none` — из самого блока `.v-card`.
- `web/src/plugins/vuetify.ts` — `defaults.VCard = { ripple: false }` (flat-язык, Material-волна не нужна; подсветка идёт обводкой).

**Как применять на странице:**
- навигационная карточка → `<VCard variant="flat" link :to="path">` (рендерится `<a>`, фокус/Enter нативные);
- карточка с действием/вложенными кнопками → `<VCard variant="flat" link role="button" tabindex="0" @click @keydown.enter>` (рендерится `div`, `<a>` нельзя из-за вложенных `<button>`/`<VBtn>`; вложенные действия гасят клик через `@click.stop`);
- скелетон-плейсхолдер тоже `<VCard variant="flat">` (без `link`) — иначе не получит дефолтные border/bg;
- в scoped-CSS оставляем только layout (`display/flex/gap/padding`), а surface/border/radius/hover/focus НЕ дублируем.

**Мигрированы (бывшие `.xxx-card` button/article → VCard):** ReportsIndexView (`.ri-index__card`), DesignSystemIndexView (`.ds-index__card`), GeoIndexView (`.geo-card`), TasksView (`.task-card` + скелетон), AgentsView (`.agent-card`, убран `--clickable`, + скелетон), TaggingRulesView (`.rule-card`).

**НЕ мигрирован McpView** (`.mcp-card`) — он уже `VCard variant="outlined"` и это раскрывающаяся панель (кликабелен только `.mcp-card__header` → `toggleExpand`), а не whole-card navigation; под дефолт `.v-card--link` не подпадает.

Терминология: плоская карточка с обводкой без тени = **outlined/flat**, НЕ «плавающая». «Плавающая» (elevated, с тенью) зарезервирована для оверлеев (меню, диалоги, поповеры) — тень там несёт смысл «над страницей». См. [[frontend_rules]].
