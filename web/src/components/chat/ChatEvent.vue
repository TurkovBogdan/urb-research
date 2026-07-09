<script setup lang="ts">
defineProps<{
  time?: string
}>()
</script>

<template>
  <div class="chat-event">
    <span class="chat-event__dot" />
    <span class="chat-event__text"><slot /></span>
    <span v-if="time" class="chat-event__time">{{ time }}</span>
  </div>
</template>

<style scoped>
.chat-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  font-size: 11px;
  color: var(--text-faint);
  font-style: italic;
}

.chat-event__dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--text-faint);
  flex-shrink: 0;
}

.chat-event__text { flex: 1; }

.chat-event__time {
  font-size: 10px;
}
</style>
