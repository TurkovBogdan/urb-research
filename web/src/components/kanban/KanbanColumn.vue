<script setup lang="ts">
import { IconPlus } from '@tabler/icons-vue'

// One board column: fixed width, header (colored dot + title + count + #actions slot),
// vertical card stack (default slot), optional dashed "add" footer (emits `add`).
withDefaults(defineProps<{
  title: string
  count?: number
  /** Header dot color — any CSS color (defaults to the faint text color). */
  tone?: string
  /** When set, renders a dashed footer button with this label; click → `add`. */
  addLabel?: string
}>(), {
  tone: 'var(--text-faint)',
})

defineEmits<{ add: [] }>()
</script>

<template>
  <div class="kanban-column">
    <div class="kanban-column__head">
      <span class="kanban-column__dot" :style="{ background: tone }" />
      <span class="kanban-column__title"><slot name="title">{{ title }}</slot></span>
      <span v-if="count !== undefined" class="kanban-column__count">{{ count }}</span>
      <VSpacer />
      <slot name="actions" />
    </div>

    <div class="kanban-column__cards">
      <slot />

      <button v-if="addLabel" type="button" class="kanban-column__add" @click="$emit('add')">
        <IconPlus :size="15" />
        {{ addLabel }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.kanban-column {
  flex: 0 0 340px;
  width: 340px;
  display: flex;
  flex-direction: column;
  /* White tray holding grey cards. */
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  max-height: 100%;
}

/* Phones (< sm, targeting 360): widen the column to nearly fill the screen so one
   column dominates with a peek of the next, instead of a cramped fixed 288px. */
@media (max-width: 599px) {
  .kanban-column {
    flex-basis: calc(100vw - 48px);
    width: calc(100vw - 48px);
  }
}

.kanban-column__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 12px 10px;
}

.kanban-column__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.kanban-column__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.kanban-column__count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  background: var(--input-bg);
  border-radius: var(--radius-sm);
  padding: 0 6px;
  line-height: 18px;
}

.kanban-column__cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 10px 12px;
  overflow-y: auto;
}

.kanban-column__add {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px;
  font-size: 12px;
  color: var(--text-faint);
  background: transparent;
  border: 1px dashed var(--border-soft);
  border-radius: var(--radius);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.kanban-column__add:hover {
  color: var(--accent);
  border-color: var(--accent);
}
</style>
