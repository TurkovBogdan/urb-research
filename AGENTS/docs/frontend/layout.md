# Frontend — Layout Layer

## Структура `src/layout/`

```
src/layout/
  store.ts                  ← Pinia layout store
  components/
    AppSidebar.vue          ← сайдбар приложения
    PageHeader.vue          ← шапка страницы
  templates/
    PageLayout.vue          ← обёртка контентной зоны
```

`components/` — UI-куски, монтируемые напрямую в `App.vue` или страницы.
`templates/` — обёртки со слотами, используемые внутри страниц.

---

## store.ts

```ts
const collapsed     = ref(readCollapsed())  // сайдбар свёрнут (rail); persist в localStorage 'app.sidebar_collapsed'
const showTopBar    = ref(true)             // показывать toolbar страницы
const showBottomBar = ref(true)             // показывать footer страницы
const mobileOpen    = ref(false)            // mobile: открыт temporary-overlay сайдбара (не persist)

// Mobile action sheet (кросс-страничный bottom sheet, см. memory mobile-action-sheet-pattern)
const mobileActionsActive    = ref(false)   // показать глобальный FAB в App.vue
const mobileActionsOpen      = ref(false)   // слайд-ап открыт
const mobileActionsIcon      = shallowRef<Component | null>(null)  // иконка триггера
const mobileActionsComponent = shallowRef<Component | null>(null)  // панель (рендерится <component :is>)
const mobileActionsCount     = ref(0)       // бейдж активных фильтров
// + registerMobileActions(icon, component) / clearMobileActions()
```

Страница регистрирует панель через composable `useMobileActions` (не `<Teleport>` — teleport из KeepAlive+transition-страницы рушит patch Vue).

Импорт: `import { useLayoutStore } from '@/layout/store'`

---

## AppSidebar.vue

Монтируется в `App.vue`. Содержит всю логику навигации.

**Навигация задаётся двумя массивами внутри компонента:**
- `nav: NavEntry[]` — основные пункты (верхняя зона)
- `navBottom: NavLink[]` — служебные пункты (нижняя зона, через `#append`)

**Иконки** — Tabler `FunctionalComponent`, тип `TablerIcon` из `src/shared/nav.ts`.

**Свёрнутый режим** (`layout.collapsed = true`, ширина 56px):
- Плоский список из `flatNav` (группы разворачиваются в дочерние ссылки)
- Иконки по центру: grid-override `grid-template-columns: 1fr` на item
- `VTooltip location="end"` с кастомным классом `sidebar-tooltip` и стрелкой влево

**Раскрытые группы** — Vuetify `VListGroup`; дефолтный indent (56px) переопределён:
```scss
.v-list-group__items > .nav-item {
  padding-inline-start: 24px !important;
}
```

---

## PageHeader.vue

Шапка страницы. Используется на всех страницах кроме Debug.

```vue
<PageHeader title="Заголовок" description="Краткое описание">
  <template #actions>
    <VBtn>...</VBtn>
  </template>
</PageHeader>
```

**Props:**
| Prop | Тип | Обязательный | Описание |
|------|-----|-------------|----------|
| `title` | `string` | да | заголовок |
| `description` | `string` | нет | подзаголовок |
| `backTo` | `RouteLocationRaw` | нет | показывает tonal-icon кнопку «назад» слева, ведёт по этому маршруту |
| `loading` | `boolean` | нет | вместо title рендерит skeleton-заглушку |

**Слоты:**
| Слот | Описание |
|------|---------|
| `#before` | заменяет зону слева (кнопку «назад»); рендерится, если есть слот или `backTo` |
| `#actions` | кнопки / контролы справа, выровнены по центру |

**Layout:** flex-строка — `#before` (кнопка назад) / левая колонка (`flex:1`: title + desc) / правая (`flex-shrink:0`: actions).

---

## PageLayout.vue

Шаблон для страниц с toolbar/footer. Читает `useLayoutStore()`.

```vue
<PageLayout>
  <template #toolbar>...</template>   <!-- скрывается если showTopBar=false -->
  <!-- контент -->
  <template #footer>...</template>    <!-- скрывается если showBottomBar=false -->
</PageLayout>
```

Сохраняет позицию скролла при `KeepAlive` (через `onBeforeRouteLeave` / `onActivated`).

**Стандарт: страница оборачивается в `<PageLayout>`** — это единственная точка управления скроллом и отступами (через `route.meta`). Технически не enforced, но routed-страницы следуют этому без исключений.

---

## route.meta — управление контентной зоной

Поведение `PageLayout` задаётся через `route.meta` в `routes.ts`:

```ts
meta: { scroll: 'y', padding: true }   // оба поля опциональны, дефолты показаны
```

| `meta.scroll` | Класс | Когда использовать |
|---|---|---|
| `'y'` (default) | `scroll-y` | Большинство страниц со списками/формами |
| `'x'` | `scroll-x` | Широкие таблицы, канбан |
| `'both'` | `scroll-both` | Редакторы, схемы |
| `'none'` | `scroll-none` | Full-height таблицы с fixed-header, split-view |

| `meta.padding` | Поведение |
|---|---|
| `true` (default) | `pa-6` добавляется к контентной зоне |
| `false` | Контент вплотную к краям, страница управляет отступами сама |

**Типичные паттерны:**
```ts
// Стандартная страница
{ path: '/administration/users', component: UsersView, meta: { scroll: 'y' } }

// Таблица на всю высоту
{ path: '/runs', component: RunsView, meta: { scroll: 'none', padding: false } }
// → внутри: <div class="d-flex flex-column h-100 pa-6"><VDataTable fixed-header height="100%" /></div>
```

---

## Цепочка высот (Vuetify 4)

**Стек:** Vuetify `4.x`, Vue `3.x`.

В Vuetify 4 `VMain` рендерит слот напрямую — без обёртки `.v-main__wrap` (которая была в Vuetify 3). Из-за этого `flex: 1 0 auto` на VMain мешает ему сжиматься до высоты вьюпорта.

Фикс в `main.scss`:
```scss
.main-content {   /* класс на VMain в App.vue */
  height: 100%;   /* резолвит к высоте v-application__wrap = viewport */
  overflow: hidden;
}
```

Полная рабочая цепочка:
```
v-application__wrap   flex-column, height: 100vh
  └─ VMain.main-content   height: 100%  ← без этого VMain растёт до content-size
       └─ <component class="h-100">     height: 100%
            └─ PageLayout   d-flex flex-column h-100 overflow-hidden
                 └─ .page-layout__content   flex-grow-1 scroll-y
                      └─ контент страницы   scrollable ✓
```

---

## Mobile navigation (2026-06-06)

Vuetify `display.mobileBreakpoint='md'` → mobile is `<960px` (matches the PageHeader 959px breakpoint).

- `AppSidebar` uses `useDisplay().mobile` → drawer `:permanent="!mobile"` / `:temporary="mobile"` +
  `v-model=drawerOpen` (getter: `true` on desktop / `layout.mobileOpen` on mobile). Rail is off on mobile
  (`collapsed = !mobile && layout.collapsed`). The logo header swaps the collapse-chevron ↔ close-X; a
  route-watcher closes the overlay on navigation.
- Mobile-only `VAppBar` in `App.vue`: hamburger → `layout.mobileOpen`, brand → `/home`, avatar-initial →
  `/profile`.
- `layout.mobileOpen` is a non-persisted store flag.

## Sidebar header divider alignment (1px gotcha)

Global `box-sizing: border-box`, so a header with `border-bottom` counts the border **inside** its
`min-height`. `AppSidebar`'s top band = logo `min-height:52` + a **separate** 1px `VDivider` → the divider
bottom sits at `y=53`. To align a bordered content-header (`.conv-side__header` in the 3 chat views) its
`min-height` must be **53** (not 52), else its divider sits 1px high. Measure with
`getBoundingClientRect().bottom` in-browser — don't eyeball.

## Icon system

Библиотека: `@tabler/icons-vue`.

**Тип иконки** (`src/shared/nav.ts`):
```ts
export type TablerIcon = FunctionalComponent<SVGAttributes>
```

**Vuetify icon set** (`src/plugins/vuetify.ts`):
- `defaultSet: 'tabler'`
- Все Vuetify-внутренние алиасы (checkboxes, arrows, etc.) замаплены на Tabler компоненты
- `markRaw()` не нужен: `FunctionalComponent` удовлетворяет Vuetify's `JSXComponent`

**Использование:**
```vue
<script setup>
import { IconArrowLeft } from '@tabler/icons-vue'
</script>
<template>
  <VBtn :icon="IconArrowLeft" />
  <VListItem :prepend-icon="IconBriefcase" />
</template>
```
