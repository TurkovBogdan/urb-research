<script setup lang="ts">
// Вид полки одной плашкой: её иконка в её цвете. Полка узнаётся по этой паре везде, где она
// упоминается — в списке полок, на плитке исследования, в заголовке раздела и в фильтре, —
// поэтому плашка живёт одним компонентом, а её размер задаёт место, куда она поставлена.
//
// Квадрат — только умолчание, а не природа плашки: в строке реестра она стоит полем во всю высоту
// соседнего текста. Поэтому задаётся ШИРИНА, от неё считаются иконка и скругление, а высота либо
// повторяет ширину, либо приходит от места (`--swatch-height`, см. `ResearchShelfMark`).
import { computed } from 'vue'

import { groupColorVars } from '../constants/groupColors'
import { iconByName } from '@/shared/icons'

const ICON_SHARE_OF_WIDTH = 0.7

const props = withDefaults(defineProps<{
  icon: string
  color: string
  /** Ширина плашки в пикселях; иконка и скругление считаются от неё. */
  width?: number
  /** Псевдо-полка («Все группы», «Без группы»): цвета у неё нет и быть не может. */
  plain?: boolean
}>(), {
  width: 20,
  plain: false,
})

const iconSize = computed(() => Math.round(props.width * ICON_SHARE_OF_WIDTH))

const boxStyle = computed(() => ({
  '--swatch-width': `${props.width}px`,
  ...(props.plain ? {} : groupColorVars(props.color)),
}))
</script>

<template>
  <span class="swatch" :class="{ 'swatch--plain': props.plain, 'color-tones': !props.plain }" :style="boxStyle">
    <component :is="iconByName(props.icon)" :size="iconSize" :stroke-width="1.7" />
  </span>
</template>

<style scoped>
.swatch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--swatch-width);
  /* Без своей высоты плашка квадратная; место, где она стоит полем рядом с текстом, задаёт её
     через `--swatch-height` — в том числе `100%` (см. `ResearchShelfMark`). */
  height: var(--swatch-height, var(--swatch-width));
  /* Скругление от ширины, а не от высоты: у вытянутой плашки высота приходит от соседнего текста
     и гуляет от строки к строке — углы гуляли бы вместе с ней. */
  border-radius: calc(var(--swatch-width) / 3);
  flex: none;
  /* Цвет полки, а без него — акцент: тот же запасной путь, что у карточки самой полки. */
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
}

.swatch--plain {
  color: var(--text-faint);
  background: var(--surface-hi);
}
</style>
