<script setup lang="ts">
// Заголовок полки над её плитками: иконка в цвете полки, имя и линейка под ними. Разделяет
// именно линейка — заголовок без неё читался бы как подпись к первой плитке, а не как начало
// раздела.
//
// Вид полки берётся из тех же реестров, что и плашка на плитке (`groupIcons` / `groupColors`):
// у полки один облик по всему разделу.
import { groupColorVars } from '../constants/groupColors'
import { groupIcon } from '../constants/groupIcons'

const props = defineProps<{
  title: string
  icon: string
  color: string
  /** Не разложенные — псевдо-полка: своего вида у неё нет, поэтому иконка и цвет запасные. */
  ungrouped?: boolean
}>()
</script>

<template>
  <div class="group-heading">
    <div class="group-heading__row color-tones" :style="groupColorVars(props.color)">
      <span class="group-heading__icon" :class="{ 'group-heading__icon--plain': props.ungrouped }">
        <component :is="groupIcon(props.icon)" :size="16" :stroke-width="1.7" />
      </span>
      <h3 class="group-heading__title">{{ props.title }}</h3>
    </div>
    <VDivider />
  </div>
</template>

<style scoped>
.group-heading {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-heading__row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.group-heading__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  flex: none;
  /* Цвет полки, а без него — акцент: тот же запасной путь, что у карточки полки и плашки. */
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
}

/* У не разложенных полки нет, и цвет здесь означал бы принадлежность к ней. */
.group-heading__icon--plain {
  color: var(--text-faint);
  background: var(--surface-hi);
}

.group-heading__title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
