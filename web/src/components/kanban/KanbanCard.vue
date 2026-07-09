<script setup lang="ts">
import { IconDots, IconMessageCircle, IconPaperclip } from '@tabler/icons-vue'

export type KanbanTagTone = 'accent' | 'neutral' | 'warn' | 'ok'
export type KanbanTag = { label: string; tone?: KanbanTagTone }

withDefaults(defineProps<{
  title: string
  tags?: KanbanTag[]
  comments?: number
  attachments?: number
  /** Short initials shown in the avatar chip. */
  assignee?: string
  /** Show the top-right three-dots menu trigger. Set `false` to hide it, or
      provide a `#menu` slot to replace it. */
  menu?: boolean
}>(), {
  tags: () => [],
  menu: true,
})
</script>

<template>
  <VCard variant="outlined" link class="kanban-card">
    <div class="kanban-card__top">
      <span class="kanban-card__title">{{ title }}</span>
      <slot name="menu"><IconDots v-if="menu" :size="16" class="kanban-card__menu" /></slot>
    </div>

    <div v-if="tags.length || $slots.tags" class="kanban-card__tags">
      <!-- Default: lightweight styled spans (DS kanban). Consumers can override with
           the `#tags` slot to render real VChips per the chip design system. -->
      <slot name="tags" :tags="tags">
        <span v-for="(tag, i) in tags" :key="i" class="kanban-card__tag" :class="`kanban-card__tag--${tag.tone ?? 'neutral'}`">{{ tag.label }}</span>
      </slot>
    </div>

    <slot />

    <div v-if="comments || attachments || assignee" class="kanban-card__foot">
      <span v-if="comments" class="kanban-card__meta"><IconMessageCircle :size="14" />{{ comments }}</span>
      <span v-if="attachments" class="kanban-card__meta"><IconPaperclip :size="14" />{{ attachments }}</span>
      <VSpacer />
      <span v-if="assignee" class="kanban-card__avatar">{{ assignee }}</span>
    </div>
  </VCard>
</template>

<style scoped>
.kanban-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  /* Light-grey card sitting on the white column. (!important beats the global
     `.v-card { background: var(--surface) !important }` in main.scss.) */
  background: var(--surface-hi) !important;
  border-color: var(--border-soft);
}

.kanban-card__top {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.kanban-card__title {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  color: var(--text);
  flex: 1;
}

.kanban-card__menu {
  color: var(--text-faint);
  flex-shrink: 0;
  margin-top: 1px;
}

.kanban-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.kanban-card__tag {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-radius: var(--radius-sm);
  padding: 1px 7px;
  line-height: 16px;
}
.kanban-card__tag--accent  { color: var(--accent); background: var(--accent-soft); }
.kanban-card__tag--neutral { color: var(--text-faint); background: var(--input-bg); }
.kanban-card__tag--warn    { color: rgb(var(--v-theme-warning)); background: rgba(var(--v-theme-warning), 0.12); }
.kanban-card__tag--ok      { color: rgb(var(--v-theme-success)); background: rgba(var(--v-theme-success), 0.12); }

.kanban-card__foot {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kanban-card__meta {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: var(--text-faint);
}

.kanban-card__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-soft);
}
</style>
