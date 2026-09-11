<script setup lang="ts">
// Выбор иконки из фиксированного набора: серая панель, внутри неё поиск и плитки с прокруткой.
//
// Набор приходит пропом, а не берётся из реестра: компонент общий, а реестров может быть
// несколько (сегодня — палитра полок research). Резолвер имени в компонент тоже проп по той же
// причине — рантайм-поиск по всему @tabler/icons-vue утащил бы в бандл ~6000 компонентов.
//
// Ищем ПО КОДУ (`building-factory-2`), а не по переводу: код — то, что уходит в базу, искать по
// нему однозначно, и второго словаря на 120 строк не нужно. Сам код наружу не печатаем: человек
// выбирает рисунок, а не строку, и выбранное видно по подсветке плитки.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconSearch } from '@tabler/icons-vue'
import type { TablerIcon } from '@/shared/nav'

const props = withDefaults(defineProps<{
  /** Выбранный код иконки; `null` — ничего не выбрано. */
  modelValue?: string | null
  /** Полный набор кодов в порядке показа. */
  icons: string[]
  /** Код → компонент. Неизвестный код резолвер обязан покрыть сам (запасной иконкой). */
  resolve: (name: string) => TablerIcon
  /** Высота области плиток; за ней она прокручивается. Поиск остаётся на месте. */
  height?: number | string
  /** Снять лоток: панель рисует тот, кто вкладывает пикер в свою (см. IconColorPicker). */
  bare?: boolean
}>(), {
  modelValue: null,
  height: 220,
  bare: false,
})

const emit = defineEmits<{ 'update:modelValue': [string] }>()

const { t } = useI18n()

const query = ref('')

const visible = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return needle ? props.icons.filter(name => name.includes(needle)) : props.icons
})

const scrollHeight = computed(() => (
  typeof props.height === 'number' ? `${props.height}px` : props.height
))
</script>

<template>
  <div
    class="icon-picker"
    :class="{ 'icon-picker--bare': props.bare }"
    :style="{ '--picker-height': scrollHeight }"
  >
    <div class="icon-picker__search">
      <VTextField
        v-model="query"
        :placeholder="t('common.icon_picker.search')"
        :prepend-inner-icon="IconSearch"
        variant="outlined"
        density="compact"
        hide-details
        clearable
      />
    </div>

    <div class="icon-picker__rule" />

    <div class="icon-picker__scroll">
      <p v-if="visible.length === 0" class="icon-picker__empty">
        {{ t('common.icon_picker.empty', { query: query.trim() }) }}
      </p>

      <div v-else class="icon-picker__grid">
        <button
          v-for="name in visible"
          :key="name"
          type="button"
          class="icon-picker__tile"
          :class="{ 'icon-picker__tile--active': name === props.modelValue }"
          :title="name"
          :aria-label="name"
          :aria-pressed="name === props.modelValue"
          @click="emit('update:modelValue', name)"
        >
          <component :is="props.resolve(name)" :size="20" :stroke-width="1.6" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Панель — утопленный лоток (роль `--surface-sunken`, как у колонок канбана): плитки на нём
   читаются как лежащие сверху. Внутри три полосы: поиск, разделитель, зона прокрутки. Поиск и
   линия закреплены, уезжают только плитки. */
.icon-picker {
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  background: var(--surface-sunken);
  border: 1px solid var(--border-sunken);
  overflow: hidden;
}

/* Без лотка остаются только полосы: тот, кто вложил пикер, рисует лоток вокруг всего набора,
   и второй фон с рамкой внутри читался бы как окно в окне. */
.icon-picker--bare {
  background: none;
  border: none;
  border-radius: 0;
}

.icon-picker__search {
  padding: 10px;
}

.icon-picker__search :deep(.v-field) {
  background: var(--surface);
}

/* Линия во всю ширину лотка, а не по полям: она отделяет полосу поиска от содержимого — та же
   роль, что у линии под шапкой окна. Поэтому отступы живут в полосах, а не на самой панели. */
.icon-picker__rule {
  height: 1px;
  background: var(--border);
}

.icon-picker__scroll {
  max-height: var(--picker-height);
  overflow-y: auto;
  padding: 10px;
}

.icon-picker__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
  gap: 6px;
}

.icon-picker__tile {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  border-radius: 8px;
  color: var(--text-muted);
  background: var(--surface);
  border: 1px solid var(--border-soft);
  cursor: pointer;
  transition: color 120ms ease, background-color 120ms ease, border-color 120ms ease;
}

.icon-picker__tile:hover {
  color: var(--text);
  border-color: var(--border);
}

.icon-picker__tile:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}

/* Выбранная плитка красится акцентом — ИЛИ цветом, если пикер вложен в панель, где цвет уже
   выбран (`.color-tones` на предке подставляет роли). Наследование переменных и есть связь между
   двумя выборами: отдельного пропа под это не нужно. */
.icon-picker__tile--active,
.icon-picker__tile--active:hover {
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
  border-color: var(--gc-ink, var(--accent));
}

.icon-picker__empty {
  margin: 0;
  padding: 18px 4px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
