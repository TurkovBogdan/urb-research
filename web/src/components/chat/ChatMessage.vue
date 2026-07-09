<script setup lang="ts">
import { computed, useSlots } from 'vue'
import type { TablerIcon } from '@/shared/nav'

type Side = 'left' | 'right'
type Tone = 'accent' | 'surface' | 'muted' | 'warning' | 'error'

const props = withDefaults(defineProps<{
  side?: Side
  tone?: Tone
  author?: string
  authorIcon?: TablerIcon
  time?: string
  timeRelative?: string
  timeTitle?: string
  body?: string
  empty?: string
  width?: string
  center?: boolean
  divided?: boolean
  dividerLabel?: string
}>(), {
  side: 'left',
  tone: 'surface',
  width: '78%',
})

const slots = useSlots()

const hasBody = computed(() => !!slots.default || !!props.body)

const hasMeta = computed(() => !!props.author || !!props.authorIcon || !!slots.meta)

const bubbleClasses = computed(() => [
  `chat-msg--${props.tone}`,
  `chat-msg--tail-${props.side}`,
])
</script>

<template>
  <div
    class="chat-msg-row"
    :class="{ 'chat-msg-row--right': side === 'right', 'chat-msg-row--divided': divided }"
  >
    <div v-if="divided" class="chat-msg-divider">
      <span class="chat-msg-divider__rule" />
      <span v-if="slots.divider || dividerLabel" class="chat-msg-divider__label">
        <slot name="divider">{{ dividerLabel }}</slot>
      </span>
      <span v-if="slots.divider || dividerLabel" class="chat-msg-divider__rule" />
    </div>

    <div
      class="chat-msg-stack"
      :class="{ 'chat-msg-stack--center': center }"
      :style="{ width }"
    >
      <div class="chat-msg" :class="bubbleClasses">
        <div class="chat-msg__bubble">
          <div v-if="hasMeta" class="chat-msg__meta">
            <VIcon v-if="authorIcon" :icon="authorIcon" size="12" class="text-medium-emphasis" />
            <slot v-if="divided" name="meta" />
            <span v-if="author" class="chat-msg__author">{{ author }}</span>
            <slot v-if="!divided" name="meta" />
          </div>

          <div v-if="hasBody" class="chat-msg__body">
            <slot>{{ body }}</slot>
          </div>
          <div v-else-if="empty" class="chat-msg__empty">{{ empty }}</div>

          <span v-if="time" class="chat-msg__time" :title="timeTitle">
            {{ time }}
            <span v-if="timeRelative" class="chat-msg__time-rel">· {{ timeRelative }}</span>
          </span>
        </div>
      </div>

      <div v-if="slots.attachments" class="chat-msg-stack__attachments">
        <slot name="attachments" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-msg-row {
  display: flex;
  width: 100%;
  justify-content: flex-start;
}

.chat-msg-row--right {
  justify-content: flex-end;
}

/* Notes break out of the centered column: a full-bleed dashed rule (with an optional centered
   caption) above and a matching rule below span the whole chat width, while the note itself
   stays within the column. */
.chat-msg-row--divided {
  flex-direction: column;
  align-items: stretch;
  margin-block: 20px;
  padding-bottom: 32px;
  border-bottom: 1px dashed rgba(var(--v-theme-on-surface), 0.22);
}

.chat-msg-row--divided .chat-msg-stack {
  margin-inline: auto;
}

/* Consecutive notes form one group bounded by a single pair of rules: the preceding note drops
   its bottom border and the following note drops its top divider, so no line falls between them. */
.chat-msg-row--divided:has(+ .chat-msg-row--divided) {
  border-bottom: none;
  padding-bottom: 0;
}

.chat-msg-row--divided + .chat-msg-row--divided {
  margin-top: calc(-1 * var(--chat-feed-gap, 16px) + 4px);
  padding-top: 0;
}

.chat-msg-row--divided + .chat-msg-row--divided .chat-msg-divider {
  display: none;
}

/* A note is bare between its dashed rules — no bubble background, shadow, tail, padding or border. */
.chat-msg-row--divided .chat-msg {
  filter: none;
}

.chat-msg-row--divided .chat-msg::after {
  display: none;
}

.chat-msg-row--divided .chat-msg__bubble {
  background: none;
  border: none;
  border-radius: 0;
  padding: 0;
}

.chat-msg-row--divided .chat-msg__body {
  color: var(--text-muted);
  white-space: normal;
}

.chat-msg-divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.chat-msg-divider__rule {
  flex: 1 1 0;
  height: 0;
  border-top: 1px dashed rgba(var(--v-theme-on-surface), 0.22);
}

.chat-msg-divider__label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-style: italic;
  color: var(--text-faint);
  white-space: nowrap;
}

.chat-msg-stack {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-msg-stack--center {
  align-self: center;
}

.chat-msg-stack__attachments {
  margin-top: 12px;
}

/* The carrier holds the side tail (::after) and the shadow. The shadow is a `drop-shadow`
   filter rather than `box-shadow` so it follows the combined silhouette of the bubble + tail
   as one shape, instead of drawing a rectangle behind the bubble that ignores the tail. */
.chat-msg {
  position: relative;
  max-width: 100%;
  min-width: 0;
  --bubble-bg: rgb(var(--v-theme-surface));
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.06)) drop-shadow(0 2px 8px rgba(0, 0, 0, 0.05));
}

/* The inner bubble owns the background, padding and rounded corners, and clips its content
   (e.g. an email iframe) to those corners — overflow lives here, off the carrier, so it never
   trims the protruding tail. */
.chat-msg__bubble {
  position: relative;
  min-width: 0;
  padding: 10px 14px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
  background: var(--bubble-bg);
}

/* A rendered email (iframe) is width:100%, but the bubble is shrink-to-fit — that makes
   the width depend on the email's own content, so it collapses/jumps when the body loads
   or remote content is revealed. Pin email bubbles to the full stack width so they stay stable. */
.chat-msg:has(.email-frame) {
  width: 100%;
}

.chat-msg:has(.email-frame) .chat-msg__bubble {
  width: 100%;
}

/* The tail is a triangle pinned to the bottom corner on the message's own side, sharing the
   bubble background so it reads as an extension of the corner. The matching bottom corner is
   squared so the tail merges into a flat edge instead of meeting a curve. */
.chat-msg::after {
  content: '';
  position: absolute;
  bottom: 0;
  width: 0;
  height: 0;
  border-style: solid;
}

.chat-msg--tail-right .chat-msg__bubble { border-bottom-right-radius: 3px; }
.chat-msg--tail-left .chat-msg__bubble { border-bottom-left-radius: 3px; }

.chat-msg--tail-right::after {
  right: -8px;
  bottom: 8px;
  border-width: 2px 0 8px 8px;
  border-color: transparent transparent transparent var(--bubble-bg);
}

.chat-msg--tail-left::after {
  left: -8px;
  bottom: 8px;
  border-width: 2px 8px 8px 0;
  border-color: transparent var(--bubble-bg) transparent transparent;
}

/* A flat, light role tint shared by the bubble and its tail (both read `--bubble-bg`).
   Client → plain white surface, team → blue, automation → gray, notes → amber. */
.chat-msg--surface { --bubble-bg: rgb(var(--v-theme-surface)); }
.chat-msg--accent { --bubble-bg: rgba(58, 136, 228, 0.12); }
.chat-msg--muted { --bubble-bg: rgba(120, 120, 120, 0.10); }
.chat-msg--warning { --bubble-bg: rgba(var(--v-theme-warning), 0.12); }
.chat-msg--error { --bubble-bg: rgba(var(--v-theme-error), 0.12); }

.chat-msg__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.chat-msg__author {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.chat-msg__body {
  font-size: 13px;
  line-height: 1.55;
  overflow-wrap: anywhere;
  color: var(--text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.chat-msg__empty {
  font-size: 12px;
  color: var(--text-faint);
  font-style: italic;
}

.chat-msg__time {
  font-size: 10px;
  color: var(--text-faint);
  align-self: flex-end;
  margin-top: 2px;
  white-space: nowrap;
}

.chat-msg__time-rel {
  margin-left: 2px;
  color: var(--text-faint);
}
</style>
