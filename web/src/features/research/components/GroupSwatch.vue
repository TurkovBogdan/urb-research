<script setup lang="ts">
// Вид полки одной плашкой: её иконка в её цвете. Полка узнаётся по этой паре везде, где она
// упоминается — в списке полок, на плитке исследования, в заголовке раздела и в фильтре, —
// поэтому квадрат живёт одним компонентом, а размер задаёт место, куда он поставлен.
import { computed } from 'vue'

import { groupColorVars } from '../constants/groupColors'
import { groupIcon } from '../constants/groupIcons'

const props = withDefaults(defineProps<{
  icon: string
  color: string
  /** Сторона квадрата в пикселях; иконка и скругление считаются от неё. */
  size?: number
  /** Псевдо-полка («Все группы», «Без группы»): цвета у неё нет и быть не может. */
  plain?: boolean
}>(), {
  size: 20,
  plain: false,
})

const boxStyle = computed(() => ({
  '--swatch-size': `${props.size}px`,
  ...(props.plain ? {} : groupColorVars(props.color)),
}))
</script>

<template>
  <span class="swatch" :class="{ 'swatch--plain': props.plain, 'color-tones': !props.plain }" :style="boxStyle">
    <component :is="groupIcon(props.icon)" :size="Math.round(props.size * 0.7)" :stroke-width="1.7" />
  </span>
</template>

<style scoped>
.swatch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--swatch-size);
  height: var(--swatch-size);
  border-radius: calc(var(--swatch-size) / 3);
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
