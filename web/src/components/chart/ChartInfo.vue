<script setup lang="ts">
import { IconInfoCircle } from '@tabler/icons-vue'

// Иконка-пояснение про источник данных диаграммы (как у KPI-метрик).
defineProps<{ text: string }>()
</script>

<template>
  <span class="chart-info">
    <VTooltip location="top" max-width="280">
      <template #activator="{ props }">
        <IconInfoCircle v-bind="props" :size="15" :stroke-width="1.6" />
      </template>
      <span>{{ text }}</span>
    </VTooltip>
  </span>
</template>

<style scoped>
.chart-info {
  display: inline-flex;
  color: var(--accent);
  cursor: help;
  opacity: 0.7;
  transition: opacity 0.15s;
}
.chart-info:hover {
  opacity: 1;
}
</style>
