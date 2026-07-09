<script setup lang="ts">
import { IconExternalLink } from '@tabler/icons-vue'

defineProps<{
  url: string
  title: string
  subtitle?: string
}>()
</script>

<template>
  <a :href="url" target="_blank" rel="noopener noreferrer" class="source-link-row">
    <span class="source-link-row__icon"><VIcon :icon="IconExternalLink" size="16" /></span>
    <span class="source-link-row__body">
      <span class="source-link-row__title">{{ title }}</span>
      <span v-if="subtitle" class="source-link-row__sub">{{ subtitle }}</span>
    </span>
  </a>
</template>

<style scoped>
.source-link-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  color: var(--text);
  text-decoration: none;
  transition: background 0.12s ease;
}

.source-link-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.source-link-row__icon {
  flex: none;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

.source-link-row__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.source-link-row__title {
  font-size: 12px;
  font-weight: 500;
  word-break: break-all;
}

.source-link-row__sub {
  font-size: 11px;
  color: var(--text-faint);
}
</style>
