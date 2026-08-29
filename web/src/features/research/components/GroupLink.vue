<script setup lang="ts">
// Полка исследования строкой: иконка в её цвете плюс имя, и то и другое уводит на саму полку.
// Тот же облик, что у плашки на плитке исследования (`groupIcons` / `groupColors`) — полка
// узнаётся по паре «иконка + цвет» везде, где упомянута.
//
// Адрес полки лежит в том же сегменте, что и исследование, и разведён префиксом кода
// (`GROUP@…` — см. `routes.ts`), поэтому ссылка собирается из кода как есть.
import { groupColorVars } from '../constants/groupColors'
import { groupIcon } from '../constants/groupIcons'

const props = withDefaults(defineProps<{
  code: string
  name: string
  icon: string
  color: string
  /** Псевдо-полка («Без группы»): своего цвета у неё нет и быть не может — иконка приглушена. */
  plain?: boolean
}>(), {
  plain: false,
})
</script>

<template>
  <RouterLink
    :to="`/research/researches/${props.code}`"
    class="group-link"
    :class="props.plain ? 'group-link--plain' : 'color-tones'"
    :style="props.plain ? undefined : groupColorVars(props.color)"
  >
    <component :is="groupIcon(props.icon)" :size="14" :stroke-width="1.7" class="group-link__icon" />
    <span class="group-link__name">{{ props.name }}</span>
  </RouterLink>
</template>

<style scoped>
.group-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.14s ease;
}

.group-link:hover {
  color: var(--text);
}

/* Цвет несёт иконка, а не имя: тон выбран под плашку и текстом читался бы хуже подписи.
   Без цвета — акцент, как везде, где полка нарисована. */
.group-link__icon {
  color: var(--gc-ink, var(--accent));
  flex: none;
}

/* Полка-остаток: цвет тут означал бы принадлежность к ней, а её никто не выбирал. */
.group-link--plain .group-link__icon {
  color: var(--text-faint);
}

.group-link__name {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
