<script setup lang="ts">
defineProps<{
  color?: 'accent' | 'success' | 'error' | 'warn' | 'muted'
  pulse?: boolean
}>()
</script>

<template>
  <span class="status-badge" :class="`status-badge--${color ?? 'muted'}`">
    <span class="status-badge__dot" :class="{ 'status-badge__dot--pulse': pulse }" />
    <slot />
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.status-badge__dot--pulse {
  box-shadow: 0 0 6px currentColor;
}

.status-badge--accent        { color: var(--accent);         background: var(--accent-soft); }
.status-badge--success       { color: var(--success);         background: var(--success-soft); }
.status-badge--error         { color: var(--error);          background: var(--error-soft); }
.status-badge--warn          { color: var(--warn);           background: var(--warn-soft); }
.status-badge--muted         { color: var(--text-muted);     background: var(--border); }
</style>
