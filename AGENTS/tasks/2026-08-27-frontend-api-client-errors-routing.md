---
title: Порт клиента API и системы уведомлений об ошибках из portal-mk2 + починка маршрутизации
date: 2026-08-27
status: in-work
description: "Перенести во фронт urb-research слой запросов и показа отказов из донора (semaphore-portal-local, resources/js/api/client/createClient.ts + errorText + useToasts/ToastStack), привести маршрутизацию и переходы по страницам в порядок. Донор — за cookie-сессией и CSRF; urb-research без авторизации, поэтому переносится не всё."
tags: [frontend, api-client, routing, errors]
---

## Task

«Изучай фронт в браузере, так-же режимы отображения. Посмотри код контроллера запросов вот тут:
`/mnt/store-dev/projects/semaphore/semaphore-portal-local/projects/portal/project/resources/js/api/client/` и систему
уведомлений об ошибках запросов. Нужно перенести суда эту систему и поправить маршрутизацию + переходы по страницам.»

## Context

### Донор (portal-mk2)

- `api/client/createClient.ts` — фабрика клиента на зону. Помимо cookie-сессии/CSRF несёт слой, не связанный с авторизацией:
  потолок ожидания (`deadline` с раздельным диагнозом timeout/aborted), `redirect: 'manual'` (за редиректом не идут),
  проверка контракта ответа (только JSON, иначе `ApiError` с кодом `protocol`), чтение тела под тем же потолком,
  `retryAfter` из `Retry-After` у 429, единая точка выхода ошибки `raise()` = «доложить + бросить».
- `shouldReport(error, opts)` — правило, что показывать человеку: 401/403/422 и `aborted`/`session_lost` — молча,
  остальное всплывает, если вызывающий не сказал `report: false`.
- `api/errorText.ts` — текст отказа: сначала свой словарь `common.errors.<code>`, затем `message` бэкенда, затем общий текст;
  у 429 — `throttled_wait` с секундами.
- `composables/useToasts.ts` + `components/ToastStack.vue` — очередь всплывающих сообщений (модуль, не Pinia — пишет клиент
  API вне компонентов): дедуп по «текст+уровень», потолок очереди 3 (вытесняются самые старые), показ по одному,
  собственный отсчёт по отметке времени + кольцо у крестика, пауза по наведению.
- `constants/errors.ts` + `composables/useShellError.ts` + `router/reload.ts` — каталог экранов отказа, показ экрана
  ВМЕСТО содержимого без смены адреса, перезагрузка на тот же путь при провале ленивого чанка после выкладки.

### Доктрина (уже исследована и лежит в этой же базе)

`RESEARCH@c1761afd0a83afede5ee0b` «Глобальные экраны ошибок портала» — области B (каталог: экран / состояние / тост)
и C (фронтовые паттерны SPA). Главное правило: **экран во весь контент — только когда умерла НАВИГАЦИЯ**; отказ
ОПЕРАЦИИ экрана не получает никогда (ответ рядом с действием). «Сущности нет» — состояние внутри раздела, не экран.

### Что во фронте urb-research сегодня (baseline по коду + браузеру)

- `web/src/api/client/internal.ts` — 110 строк: нет потолка ожидания, нет `redirect: 'manual'`, нет проверки
  content-type (`JSON.parse` любого тела), нет `retryAfter`, нет единой точки показа отказа. Ошибка просто бросается.
- Показ отказов размазан: в каждом сторе `error.value = e instanceof Error ? e.message : String(e)`, в каждой вьюхе
  `<VAlert type="error">` (18 мест). Тостов нет вовсе. Отказ операции (создание запроса, сохранение настроек)
  показывается по-разному в каждой форме.
- Экранов отказа один — 404 маршрута (`views/errors/NotFoundView.vue` поверх `components/ErrorState.vue`), рисуется
  на исходном адресе (это правильно). Экранов «сбой» и «нет связи» нет; `app.config.errorHandler` не поставлен —
  исключение в рендере даёт белый экран. `router.onError` только гасит полосу прогресса → провал ленивого чанка
  после выкладки = «клик, и ничего».
- 404 сущности (`/research/researches/<битый код>`) рисует узкую красную `VAlert` под шапкой — пустая страница.
- Маршруты: ни одного `name`, навигация строками; `AppSidebar` ходит `@click="router.push(...)"` вместо `:to` →
  в разметке нет `<a>` (нет средней кнопки, «открыть в новой вкладке», клавиатуры).
- Подсветка активного пункта — `isActive` = точное совпадение пути → на деталке (`/research/researches/<code>`)
  раздел в меню не подсвечен. Для группы «Веб-поиск» используется `isUnderPath`, для верхнего уровня — нет.
- `document.title` не меняется ни на одном переходе; фокус после навигации не переносится; `aria-live` нет.
- Сплэш в `web/index.html` жёстко тёмный (`#0F1115`) — при светлой теме холодная загрузка даёт тёмную вспышку.

### Режимы отображения (проверено в браузере)

Тема (тёмная/светлая/системная), шрифт интерфейса, шрифт текста, кегль зоны чтения, ширина параграфов —
`/settings/interface`, хранение в localStorage (`stores/settings.ts`). Свёрнутый сайдбар (рельс 56px, флайаут для
групп) и мобильный режим (`VAppBar` + overlay-drawer) отрисовываются корректно.

## What was done

### Слой запросов

- `web/src/api/client/createClient.ts` — фабрика клиента на зону. Перенесена целиком, включая слой сессии
  (CSRF + двойная отправка токена, ретрай на 419, политика 401/403, стоп-кран потерянной сессии, 409
  `already_authenticated`). У internal-зоны авторизации нет, поэтому слой выключен конфигом: `csrf: false`,
  `loginPath`/`onUnauthenticated` не заданы. ⚠️ Включённый CSRF без middleware на бэкенде добавил бы
  провальный GET `/internal/csrf-cookie` перед каждой записью.
- `internal.ts` стал тонким: `createClient({prefix:'/internal', onForbidden: setShellError('forbidden'),
  onError: pushToast(errorText(...))})`. Путь импорта сохранён — 20+ вызывающих не тронуты.
- `errorText.ts` — свой словарь `common.errors.<code>` → сообщение бэкенда → общий текст; 429 с секундами.
- Политика показа `shouldReport`: молчим на 401/403/422, `aborted`/`session_lost`, `already_authenticated`
  **и на 404** (последнее — правка против донора: раздел показывает «не найдено» состоянием на своём месте,
  тост дублировал бы ту же новость; найдено живой проверкой в браузере).

### Формы отказа

- `useToasts.ts` + `ToastStack.vue` — очередь (дедуп текст+уровень, потолок 3, показ по одному), отсчёт от
  отметки времени с кольцом у крестика, пауза по наведению; тона на токенах, не на палитре Vuetify.
- `constants/errors.ts` + `useShellError.ts` + `ErrorScreen.vue` — каталог из четырёх видов отказа и показ
  экрана ВМЕСТО содержимого на исходном адресе; снимает следующая навигация (гвард).
- `SectionError.vue` — отказ чтения раздела на месте содержимого (404 отличается от сбоя по статусу).
  Заменил 8 узких `VAlert` в деталках и списках.
- Сторы держат сам отказ (`error = ref<unknown>`), а не строку: показ решает по статусу, текст берёт из
  `errorText`. Переведены 9 сторов.
- `ErrorState.vue` — выходы с экрана параметром (`back`/`home`/`retry`), фокус на заголовок, `role=alert`.
- `main.ts` — `app.config.errorHandler` → экран «что-то сломалось» вместо белого экрана.

### Маршрутизация и переходы

- Имена у всех маршрутов; `meta.title` (ключ словаря) + гвард ставит `document.title`.
- Гвард после перехода переводит фокус в зону содержимого и снимает экран отказа.
- `router/reload.ts` — `vite:preloadError` + `router.onError` → перезагрузка на целевой путь с
  предохранителем в `sessionStorage`.
- Сайдбар: `:to` вместо `router.push` (в DOM появились `<a>`), подсветка по ПРЕФИКСУ пути (на деталке
  раздел больше не «гаснет»), логотип — `RouterLink`.
- `router/design-system.ts` — 40 однотипных маршрутов свёрнуты в таблицу «сегмент → файл вьюхи» поверх
  `import.meta.glob`.

### Перенос компонентов (вторая итерация, по запросу пользователя)

- `SectionHeader.vue` — заголовок секции (уровень задаёт тег И кегль, счётчик, правый слот, плейсхолдеры).
  `PageHeader` пересобран поверх него: у страницы остаётся только кнопка «назад». Убрал `.section-title` +
  его CSS из 4 вьюх.
- `AppDialog` / `DialogHeader` / `DialogActions` / `ConfirmDialog` — перенесены как есть. Диалог создания
  запроса переведён на `AppDialog`; `createQuery` получил `report: false` (отказ показывает сама форма).
- `Callout.vue` — перенесён; заведена страница дизайн-системы (тона, зачин, плотный, сравнение с VAlert).
- Дизайн-система: новые страницы `toasts`, `callout`, `error-states` («Отказы»: таблица-правило
  сценарий→форма→кто показывает, четыре экрана через переключатель — по одному, иначе они дерутся за
  фокус, — и три состояния раздела) и `section-header` (уровни, части, уровень страницы); разделы
  `AppDialog`/`ConfirmDialog` добавлены в `dialogs`.
- Проверено: `SwitchPanel.vue` и демо чекбоксов/переключателей у нас **уже есть и совпадают с донорскими**
  побайтово — переносить нечего.

### Проверка

`vue-tsc --noEmit` — 0 ошибок; `vite build` — успешно. Живая проверка в браузере (dev :22041): 404 маршрута,
404 сущности, тосты всех уровней + очередь + sticky, ConfirmDialog, диалог создания запроса, заголовки
секций, заголовок вкладки, подсветка раздела на деталке, тёмная и светлая темы, мобильная ширина.

## Problems

- Первая версия политики показа дублировала 404: состояние в разделе + тост. Поймано живой проверкой,
  исправлено в `shouldReport`.
- `CodeBlock` принимает `lang`, а не `language` — новые демо-страницы сначала рендерили код как plain text.
- Классы витрины (`ds-page`/`ds-card`/`ds-row`) объявлены в scoped-стилях КАЖДОЙ страницы дизайн-системы,
  общих нет — новым страницам пришлось их продублировать. Кандидат на вынос.

## Result

Изменены/созданы (web/src): `api/client/createClient.ts`, `api/client/internal.ts`, `api/errorText.ts`,
`composables/useToasts.ts`, `composables/useShellError.ts`, `constants/errors.ts`,
`components/{ToastStack,ErrorScreen,SectionError,ErrorState,SectionHeader,AppDialog,DialogHeader,DialogActions,ConfirmDialog,Callout}.vue`,
`layout/components/{PageHeader,AppSidebar}.vue`, `App.vue`, `main.ts`,
`router/{index,guards,meta,reload,design-system}.ts`, `features/*/routes.ts`, 9 сторов, 10 вьюх,
`views/design-system/feedback/{ToastsView,CalloutView,DialogsView}.vue`,
`views/design-system/DesignSystemIndexView.vue`, словари `locales/ru.json` и `locales/design-system/ru.json`.

**Не доведено до конца** (осталось на старом контракте ошибок): `SettingsView`, `SetupView`, `TaskRunsView`,
`ConnectorsView`, `McpServersView`, `DocumentsTable`, сторы `core_monitoring/tasks` и `research/groups`.

⚠️ **Коллизия с параллельной задачей.** В `features/research` во время работы шла чужая задача (группы
исследований, выбор иконки): появились `groups.store.ts`, `GroupsView.vue`, `GroupView.vue`,
`ResearchesTable.vue`, `IconPickerView.vue`; словарь дизайн-системы переформатирован. Я правил в этой же
области `ResearchesView.vue`, `researches.store.ts`, `research/routes.ts` — при коммите пути придётся
разделять между задачами вручную.

⚠️ **`web/dist` пересобран** — в артефакт попала и незакоммиченная работа параллельной задачи. Коммитить
`web/dist` этой задачей нельзя, пока обе не сойдутся.
