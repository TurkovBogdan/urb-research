<script setup lang="ts">
// Полка исследования одной меткой — плашка её цвета с её иконкой.
//
// Метка, а не строка с именем: в реестре полка отвечает на вопрос «чьё это», а не «как
// называется», и на этот вопрос отвечает пара «иконка + цвет» — так полка нарисована везде.
// Имя остаётся во всплывающей подписи, потому что цвет узнаётся не с первого раза.
//
// Нажатие СУЖАЕТ список до этой полки, а не уводит на её страницу: вопрос, который задают меткой
// в реестре, — «а что тут ещё её», и ответ на него живёт на той же странице, рядом с фильтрами и
// строкой поиска, которые уже набраны.
//
// У не разложенного исследования полки нет, и метка не исчезает, а показывает псевдо-полку
// «Без группы»: сузить список до неразложенных — тоже вопрос.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import GroupSwatch from './GroupSwatch.vue'
import { UNGROUPED_CODE, type ResearchListRow } from '../api'

// Ширина плашки; высоту она берёт от соседнего текста — двух его линий, названия и описания, —
// поэтому задана не здесь, а растяжением по строке (`--swatch-height: 100%` ниже). Иконка у
// `GroupSwatch` считается от ширины: на 30px она занимает 21 и в поле высотой в две линии стоит с
// полем сверху и снизу.
const MARK_WIDTH = 30

const props = withDefaults(defineProps<{
  research: ResearchListRow
  /** Список уже сужен до одной полки (страница полки): сужать его меткой не до чего, и она
      остаётся просто меткой — без нажатия и без обещания, что по ней что-то произойдёт. */
  filterable?: boolean
}>(), {
  filterable: true,
})

const emit = defineEmits<{ filter: [code: string] }>()

const { t } = useI18n()

const shelf = computed(() => {
  const { group_code: code, group_name: name, group_icon: icon, group_color: color } = props.research
  if (!code) {
    return { code: UNGROUPED_CODE, name: t('research.group.ungrouped.title'), icon: '', color: '', plain: true }
  }
  return { code, name, icon, color, plain: false }
})
</script>

<template>
  <!-- Нажатие внутри строки-ссылки: без остановки события оно дошло бы до строки и увело на
       исследование — то есть мимо того, куда целились. -->
  <component
    :is="props.filterable ? 'button' : 'span'"
    :type="props.filterable ? 'button' : undefined"
    class="shelf-mark"
    :class="{ 'shelf-mark--static': !props.filterable }"
    :title="shelf.name"
    @click.stop="props.filterable && emit('filter', shelf.code)"
  >
    <GroupSwatch
      :icon="shelf.icon"
      :color="shelf.color"
      :plain="shelf.plain"
      :width="MARK_WIDTH"
    />
  </component>
</template>

<style scoped>
/* Ставится в строку рядом с текстом и тянется на всю её высоту, а плашка внутри тянется за ней —
   так метка равна названию с описанием, сколько бы строк они ни заняли.
   Сброс оформления кнопки: браузер рисует ей плашку с рамкой, а нужна одна фигура. */
.shelf-mark {
  --swatch-height: 100%;
  display: inline-flex;
  align-self: stretch;
  flex: none;
  appearance: none;
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  opacity: 0.9;
  transition: opacity 0.14s ease;
}

.shelf-mark:hover {
  opacity: 1;
}

/* Нечего сужать — нечего и обещать: ни курсора, ни отклика на наведение. */
.shelf-mark--static {
  cursor: default;
  opacity: 1;
}
</style>
