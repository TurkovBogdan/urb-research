<script setup lang="ts">
// Выбор цвета из фиксированного набора: лоток с плитками, одна плитка — один именованный цвет.
//
// Набор и резолвер приходят пропами по той же причине, что у IconPicker: компонент общий, а
// реестров может быть несколько (сегодня — палитра полок research). Резолвер отдаёт ступени цвета
// переменными, плитка красится ролью `--gc-swatch`, а какая ступень читаема в текущей теме,
// решает `.color-tones` в main.scss — пикер о темах не знает (см. shared/colorTones.ts).
//
// Наружу и внутрь ходит ИМЯ (`blue`), не hex: имя — то, что уходит в базу. Печатать его на
// плитке незачем (человек выбирает цвет, а не строку), поэтому оно живёт в подсказке и в
// `aria-label`, а выбранное видно по кольцу и галочке.
//
// Галочка — второй признак выбора рядом с кольцом: набор целиком состоит из цветов, и состояние,
// показанное только цветом, потерялось бы в нём.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconCheck } from '@tabler/icons-vue'
import type { ColorToneVars } from '@/shared/colorTones'

const props = withDefaults(defineProps<{
  /** Выбранное имя цвета; `null` — цвет не задан. */
  modelValue?: string | null
  /** Полный набор имён в порядке показа. */
  colors: string[]
  /** Имя → ступени цвета переменными. Неизвестное имя резолвер обязан покрыть сам. */
  resolve: (name: string) => ColorToneVars
  /** Показывать плитку «без цвета»; выбор её отдаёт `null`. */
  clearable?: boolean
  /** Сторона плитки в пикселях; от неё считается число колонок. */
  size?: number
  /** Снять лоток: панель рисует тот, кто вкладывает пикер в свою (см. IconColorPicker). */
  bare?: boolean
}>(), {
  modelValue: null,
  clearable: false,
  size: 34,
  bare: false,
})

const emit = defineEmits<{ 'update:modelValue': [string | null] }>()

const { t } = useI18n()

const tileSize = computed(() => `${props.size}px`)
</script>

<template>
  <div
    class="color-picker"
    :class="{ 'color-picker--bare': props.bare }"
    :style="{ '--tile-size': tileSize }"
  >
    <div class="color-picker__grid">
      <button
        v-if="props.clearable"
        type="button"
        class="color-picker__tile color-picker__tile--none"
        :class="{ 'color-picker__tile--active': props.modelValue === null }"
        :title="t('common.color_picker.none')"
        :aria-label="t('common.color_picker.none')"
        :aria-pressed="props.modelValue === null"
        @click="emit('update:modelValue', null)"
      >
        <IconCheck v-if="props.modelValue === null" :size="16" :stroke-width="2.4" />
      </button>

      <button
        v-for="name in props.colors"
        :key="name"
        type="button"
        class="color-picker__tile color-tones"
        :style="props.resolve(name)"
        :class="{ 'color-picker__tile--active': name === props.modelValue }"
        :title="name"
        :aria-label="name"
        :aria-pressed="name === props.modelValue"
        @click="emit('update:modelValue', name)"
      >
        <IconCheck v-if="name === props.modelValue" :size="16" :stroke-width="2.4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Лоток тот же, что у выбора иконки: утопленная панель, плитки читаются лежащими на ней.
   Полосы поиска здесь нет — набор в полтора десятка плиток виден целиком, искать нечего. */
.color-picker {
  border-radius: 10px;
  background: var(--surface-sunken);
  border: 1px solid var(--border-sunken);
  padding: 10px;
}

/* Без лотка остаётся одна сетка: панель вокруг рисует тот, кто вложил пикер, и второй фон с
   рамкой внутри читался бы как окно в окне. */
.color-picker--bare {
  background: none;
  border: none;
  border-radius: 0;
  padding: 0;
}

.color-picker__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--tile-size), 1fr));
  gap: 8px;
}

.color-picker__tile {
  background: var(--gc-swatch);
  /* Волосяная линия внутрь: в светлой теме плитка средней ступени отходит от лотка всего на
     ~2.8:1, и без края набор читается как размытое пятно. Внутрь, а не рамкой, чтобы не менять
     размер плитки и не спорить с кольцом выбора. */
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  /* Галочка кладётся на заливку, а заливка у всего набора одной светлоты (OKLCH L 0.62), поэтому
     тёмный штрих читается на любой плитке и в любой теме — худшая пара 3.93:1 при пороге 3. */
  color: rgba(0, 0, 0, 0.72);
  transition: transform 120ms ease, box-shadow 120ms ease;
}

.color-picker__tile:hover {
  transform: scale(1.06);
}

.color-picker__tile:focus-visible {
  outline: 2px solid var(--text);
  outline-offset: 2px;
}

/* Кольцо, а не рамка: рамка съела бы часть заливки, а зазор цветом лотка отделяет кольцо от
   самой плитки, и оно одинаково видно на светлой и на тёмной плитке. */
.color-picker__tile--active {
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.14), 0 0 0 2px var(--surface-sunken), 0 0 0 4px var(--text);
}

/* «Без цвета» — пустая плитка тона карточки: она не участвует в наборе как цвет, а показывает,
   что цвет не задан, поэтому и галочка на ней в цвете текста, а не тёмная. */
.color-picker__tile--none {
  background: var(--surface);
  border: 1px dashed var(--border);
  color: var(--text-muted);
  box-shadow: none;
}

.color-picker__tile--none.color-picker__tile--active {
  box-shadow: 0 0 0 2px var(--surface-sunken), 0 0 0 4px var(--text);
}
</style>
