# Vuetify 4 — CSS override patterns

## Главное правило: @layer

Vuetify 4 помещает **все** свои стили в `@layer vuetify-components`:

```css
@layer vuetify-components {
  .v-btn-group .v-btn { border-radius: 0; }
  .v-btn-group--horizontal .v-btn:first-child { border-start-start-radius: inherit; }
  /* ... */
}
```

**Незаслоённые стили (без `@layer`) всегда побеждают layered**, независимо от специфичности.

Следствие для `main.scss`: наш `.v-btn { border-radius: var(--radius-sm) }` — незаслоённый, поэтому он бьёт любое правило Vuetify, включая более специфичные `.v-btn-group .v-btn { border-radius: 0 }`.

### Когда нужен `!important`

Только для свойств, которые Vuetify пишет **inline-стилями** (через JS), а не CSS:
- `background` на `.v-application` (тема)
- `background` на `.v-navigation-drawer` (тема)
- Иногда `box-shadow` (elevation)

Для всего остального `!important` не нужен — наш незаслоённый CSS уже выигрывает.

---

## VBtn — кастомные размеры

Vuetify задаёт высоты через CSS-переменные и layered-правила. Мы переопределяем через незаслоённые правила с `!important` только для height/padding (чтобы побить и inline-вычисления):

```scss
.v-btn {
  font-family: var(--font) !important;
  font-weight: 500 !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  border-radius: var(--radius-sm);   // БЕЗ !important — иначе ломает группы

  &.v-btn--size-x-small { height: 22px !important; /* ... */ }
  &.v-btn--size-small   { height: 26px !important; /* ... */ }
  &.v-btn--size-default { height: 30px !important; /* ... */ }
  &.v-btn--size-large   { height: 36px !important; /* ... */ }
}
```

---

## VNumberInput — кнопки управления и суффикс

### Кнопки управления

Vuetify рендерит кнопки как `v-btn--size-small` или `v-btn--size-default`. Наш `height: 26px/30px !important` ломает их flex-поведение внутри контейнера.

**Решение:** сбрасываем height/min-height и даём `flex: 1` чтобы кнопки вписывались в высоту поля:

```scss
.v-number-input .v-number-input__control .v-btn {
  height: unset !important;
  min-height: unset !important;
  flex: 1 !important;
  padding-inline: 4px !important;
}
```

- `stacked` (flex-direction: column-reverse): два `flex: 1` → каждая кнопка 50% высоты поля (18px)
- `default` (flex-direction: row): два `flex: 1` → каждая 50% ширины, высота = `align-self: stretch` = 36px
- `split`: аналогично default

### Суффикс / префикс в VNumberInput (и outlined VTextField)

Vuetify в `@layer` задаёт для `.v-text-field__suffix`:
```css
min-height: max(var(--v-input-control-height, 56px), ...);  /* = 56px */
padding-bottom: var(--v-field-input-padding-bottom);         /* = 16px */
```

Для полей с `v-field--center-affix` (outlined + VNumberInput) это лишнее — суффикс должен быть центрирован, без padding для floating label.

**Решение:**
```scss
.v-field--center-affix {
  .v-text-field__suffix,
  .v-text-field__prefix {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    min-height: unset !important;
    align-self: center;
  }
}
```

---

## VBtnGroup / VBtnToggle — border-radius

Vuetify реализует скругление групп через цепочку наследования:
1. `.v-btn-group` держит `border-radius` (контейнер)
2. `.v-btn-group .v-btn { border-radius: 0 }` — все внутренние кнопки плоские
3. `:first-child { border-start-start-radius: inherit; border-end-start-radius: inherit }`
4. `:last-child { border-start-end-radius: inherit; border-end-end-radius: inherit }`

Всё это в `@layer` — и наш незаслоённый `.v-btn { border-radius }` их перебивает.

**Решение: воспроизвести механизм вне `@layer`:**

```scss
// Сбрасываем radius у всех кнопок внутри группы
.v-btn-group .v-btn { border-radius: 0; }

// Восстанавливаем скругление только на внешних углах
.v-btn-group--horizontal .v-btn:first-child {
  border-start-start-radius: inherit;
  border-end-start-radius: inherit;
}
.v-btn-group--horizontal .v-btn:last-child {
  border-start-end-radius: inherit;
  border-end-end-radius: inherit;
}
```

`VBtnToggle` расширяет `VBtnGroup`, поэтому получает те же классы (`v-btn-group--horizontal`, etc.) и те же правила применяются автоматически.

---

## VBtnGroup / VBtnToggle — высота

Vuetify задаёт в `@layer`:
```css
.v-btn-group--density-default.v-btn-group--horizontal { height: 48px; }
.v-btn-group--density-comfortable.v-btn-group--horizontal { height: 40px; }
.v-btn-group--density-compact.v-btn-group--horizontal { height: 36px; }
```

Наши кнопки — 30px. Без переопределения контейнер 48px, кнопки 30px → 18px пустого пространства снизу.

**Решение:**
```scss
.v-btn-group--horizontal { height: auto; }
```

Контейнер подстраивается под высоту кнопок. Работает для любого размера.

---

## VBtnToggle — стилизация контейнера и активного состояния

VBtnToggle не получает `variant="outlined"` по умолчанию, поэтому рамки нет. Кнопки без variant получают elevation-поверхностный фон — убираем его явно.

```scss
.v-btn-toggle {
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);   // рамка вручную, т.к. нет variant
  box-shadow: none !important;

  .v-btn { color: var(--text-muted); background: transparent !important; }
  .v-btn.v-btn--active {
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
  }
}
```

В шаблоне нужен `divided` для разделителей между кнопками:
```vue
<VBtnToggle v-model="model" mandatory divided>
  <VBtn value="a">A</VBtn>
  <VBtn value="b">B</VBtn>
</VBtnToggle>
```

---

## VBtnGroup / VBtnToggle — разделители (`divided`)

Vuetify задаёт `border-inline-end-width: thin` **без цвета** — берёт `currentColor`. В тёмной теме `currentColor` кнопки белый → белый разделитель.

**Решение:**
```scss
.v-btn-group--divided .v-btn:not(:last-child) {
  border-inline-end-color: var(--border) !important;
}
```

Работает для VBtnGroup и VBtnToggle (оба рендерятся через `v-btn-group--divided`).

---

## VField — hover-состояние

По умолчанию Vuetify осветляет рамку при ховере через `@layer`. Мы переопределяем цвет рамки и лейбла на фирменный зелёный:

```scss
.v-field {
  .v-field__outline { color: var(--border); }
  &:hover .v-field__outline            { color: var(--accent); }
  &.v-field--focused .v-field__outline { color: var(--accent); }

  .v-label { color: var(--text-muted); }
  &:hover .v-label            { color: var(--accent); }
  &.v-field--focused .v-label { color: var(--accent); }
}
```

Глобально — применяется ко всем VTextField, VSelect, VNumberInput, VAutocomplete и т.д.

---

## VNumberInput — hover кнопок управления

Кнопки управления (шевроны/± внутри поля) не имеют hover-эффекта по умолчанию. Добавляем зелёный accent:

```scss
.v-number-input .v-number-input__control .v-btn {
  // ...existing flex/height rules...
  &:hover { background: var(--accent-soft) !important; color: var(--accent) !important; }
}
```

---

## VDataTable — правильное применение стилей

Vuetify рендерит таблицу как HTML `<table>`. **`border-bottom` на `<tr>` не рендерится** — нужно ставить на `<td>`.

```scss
.v-data-table {
  background: transparent !important;  // Vuetify ставит surface как inline-style

  .v-data-table__th {
    background: var(--surface-hi) !important;   // header bg — inline → !important
    height: 36px !important;
    border-bottom: 1px solid var(--border) !important;
    // font/color/uppercase — без !important, выигрывают у @layer
  }

  .v-data-table__tr {
    td {
      border-bottom: 1px solid var(--border-soft) !important;
      padding-top: 6px !important;
      padding-bottom: 6px !important;
    }
    &:last-child td { border-bottom: none !important; }  // без двойного бордера с VCard
    &:hover td { background: oklch(0.76 0.20 136 / 0.05) !important; }  // 5% зелёного
  }
}
```

Типичный паттерн в шаблоне:
```vue
<VCard variant="outlined" rounded="lg">
  <VDataTable :headers="headers" :items="items" :items-per-page="-1"
    density="comfortable" hide-default-footer hover />
</VCard>
```

`VCard` обрезает содержимое по `border-radius`; `last-child td { border-bottom: none }` убирает двойной нижний бордер.

---

## VProgressCircular / VProgressLinear — цвет

Vuetify ставит `color` как **inline-style** (не через CSS-класс) → нужен `!important`.

```scss
// Blanket override — class text-primary не добавляется без явного color prop
.v-progress-circular { color: var(--accent) !important; }

// Кнопочный spinner должен наследовать цвет кнопки, а не accent
.v-btn .v-btn__loader .v-progress-circular { color: inherit !important; }

.v-progress-linear {
  color: var(--accent) !important;  // наследуется indeterminate-барами через currentColor
  .v-progress-linear__background  { background: var(--border-soft) !important; }
  .v-progress-linear__determinate { background: var(--accent) !important; }
}
```

---

## VSkeletonLoader — цвет костей

У `VSkeletonLoader` **нет собственной переменной цвета** — кость берёт `--v-theme-on-surface` с альфой. Наш `theme.variables` ставит `border-opacity: 1`, из-за чего альфа теряется и кость выходит сплошным тёмным `on-surface`. Менять тему нельзя (сломает контраст текста), поэтому перекрываем цвет глобально в `main.scss`:

```scss
.v-skeleton-loader {
  background: transparent;

  .v-skeleton-loader__bone { background: var(--border-soft); }   // листовая кость — серая
  // кость-обёртка (содержит вложенные кости) → прозрачна, серыми остаются только листья
  .v-skeleton-loader__bone:has(.v-skeleton-loader__bone) { background: transparent; }
  .v-skeleton-loader__bone::after {
    background: linear-gradient(90deg, transparent, rgb(255 255 255 / 65%), transparent);
  }
}
```

Без `:has()`-правила контейнерные пресеты (`paragraph`, `article`, `card`) красятся целиком и схлопывают строки в один блок.

> **Ширина.** Корень `.v-skeleton-loader` — `inline-flex`, поэтому в block-контейнере полноширинные кости (`text`/`heading`/`image`) схлопываются в 0. Это **не** глобальный override — задаётся локально там, где нужно (`width: 100%` на корне), т.к. зависит от раскладки страницы.

---

## VSwitch — кастомизация inset-переключателя

### Размеры через SASS-переменные (`settings.scss`)

```scss
@forward 'vuetify/settings' with (
  $switch-inset-track-width:      34px,   // default: 52px
  $switch-inset-track-height:     20px,   // default: 32px
  $switch-inset-thumb-width:      12px,   // default: 24px
  $switch-inset-thumb-height:     12px,
  $switch-inset-thumb-off-width:  12px,   // = ON — без уменьшения в OFF-состоянии
  $switch-inset-thumb-off-height: 12px,
  $switch-track-opacity:          1,      // default: 0.6
);
```

Файл подключён через `vite-plugin-vuetify`: `styles: { configFile: 'src/styles/settings.scss' }`.
Использовать `@forward`, не `@use` — иначе плагин не видит переопределения.

### Цвет трека — `:has()` вместо color prop

Vuetify ставит цвет трека через класс `bg-primary` из `@layer vuetify-components`. Наш CSS незаслоённый — выигрывает. Для OFF/ON состояний используем `:has()`:

```scss
.v-switch {
  &:has(input:not(:checked)) .v-switch__track { background: var(--border); }
  &:has(input:checked)       .v-switch__track { background: var(--accent); }
}
```

**Почему `--accent`, а не `color prop`:** Vuetify использует `rgb(74, 222, 128)` (sRGB) из `--v-theme-primary`. Наш `--accent = oklch(0.76 0.2 136)` рендерится ярче на P3-дисплеях (Mac Retina). Чекбоксы используют `currentColor` → oklch напрямую. Чтобы не было визуального расхождения, переключатель тоже ставим в oklch.

### Цвет thumb — только CSS, SASS-переменная не работает

`$switch-thumb-background` в Vuetify 4 **игнорируется** — в SASS-исходнике хардкодено `rgb(var(--v-theme-surface-bright))`. Переопределяем через CSS:

```scss
.v-switch .v-switch__thumb { background: #fff; box-shadow: none; }
```

### Позиция thumb — CSS translateX (SASS-переменная не помогает)

**Проблема:** Vuetify компилирует translation контейнера thumb из дефолтных размеров: `52/2 - 24/2 - 2 = ±12px`. Даже с нашим thumb=12px контейнер `.v-selection-control__input` остаётся 40px (определяется размером ripple-зоны, не thumb), поэтому SASS не пересчитывает translation.

**Геометрия (track=34px, container=40px, thumb=12px):**
- Container base position = `(34 - 40) / 2 = -3px` от левого края трека
- Thumb center в container = `(40 - 12) / 2 = 14px` от левого края контейнера
- Желаемый gap = 4px со всех сторон (= `(20 - 12) / 2` — совпадает с вертикальным)

```
OFF: thumb.left = 4px → container.left = 4 - 14 = -10px → translateX = -10 - (-3) = -7px
ON:  thumb.left = 34 - 4 - 12 = 18px → container.left = 18 - 14 = 4px → translateX = 4 - (-3) = +7px
```

**Переопределение (незаслоённый CSS бьёт `@layer`):**

```scss
.v-switch {
  .v-selection-control__input                             { transform: translateX(-7px); }
  .v-selection-control--dirty .v-selection-control__input { transform: translateX(7px); }
}
```

> При изменении размеров нужно пересчитывать translation вручную по формуле выше.
> `$switch-thumb-offset` в settings.scss не влияет на translation — оставлен как документация намерений.

---

## VSlider / VRangeSlider — цвет трека

Vuetify рендерит трек двумя элементами:
- `.v-slider-track__fill` — заполненная (активная) часть, `bg-primary` без opacity
- `.v-slider-track__background` — фоновая (неактивная) часть, `bg-primary` + `opacity: 0.38` (`$disabled-opacity`)

Оба используют `rgb(74, 222, 128)` (sRGB). На P3-дисплеях fill выглядит иначе, чем oklch-акцент на других элементах.

**Решение:** таргетируем только `.bg-primary` — не трогаем цветные слайдеры (`color="error"` → `bg-error` и т.д.):

```scss
.v-slider-track__fill.bg-primary       { background: var(--accent); }
.v-slider-track__background.bg-primary { background: var(--accent-mid); opacity: 1; }
```

`--accent-mid = oklch(0.76 0.20 136 / 0.25)` — приглушённый фирменный, заменяет `opacity: 0.38` на sRGB.

---

## VBtnGroup — outlined + divided

```vue
<VBtnGroup variant="outlined" divided>
  <VBtn>Назад</VBtn>
  <VBtn>Далее</VBtn>
</VBtnGroup>
```

CSS только для цвета рамки и убирания тени:
```scss
.v-btn-group {
  border-radius: var(--radius-sm);
  border-color: var(--border) !important;
  box-shadow: none !important;
}
```
