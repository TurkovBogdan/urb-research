<script setup lang="ts">
// A quiet tinted panel of explanatory text, tied to its context — the industry's "callout"
// (Primer / Radix / shadcn; "admonition" in docs systems). Typical use: under a form control,
// explaining what the chosen option means.
//
// NOT a VAlert. An alert reports an EVENT (something failed, something needs attention) and is
// often dismissible; a callout is permanent context that was always going to be there. Keeping
// them apart matters: if explanations look like alerts, real alerts stop being noticed.
//
// Tones match StatusBadge's vocabulary so the whole UI speaks one colour language. `info` is the
// default and the right choice for plain explanation — reach for `warn`/`error` only when the
// text genuinely carries consequence.
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  tone?: 'info' | 'warn' | 'error' | 'muted'
  /** Optional bold lead-in above the body. */
  title?: string
  /** Tabler icon component; omit for a text-only callout. */
  icon?: unknown
  /** Compact padding/type — for sitting tight under an input. */
  dense?: boolean
}>(), {
  tone: 'info',
  title: undefined,
  icon: undefined,
  dense: false,
})

const classes = computed(() => [
  `callout--${props.tone}`,
  { 'callout--dense': props.dense },
])
</script>

<template>
  <div class="callout" :class="classes">
    <!-- The icon rides in a box as tall as one line of text, so it centres on the FIRST line at
         any size — a fixed margin only ever looks right for one font-size/line-height pair. -->
    <span v-if="icon" class="callout__icon">
      <component :is="icon" :size="dense ? 14 : 16" />
    </span>
    <div class="callout__body">
      <strong v-if="title" class="callout__title">{{ title }}</strong>
      <div class="callout__text"><slot /></div>
    </div>
  </div>
</template>

<style scoped>
.callout {
  --callout-line: 1.45;

  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--callout-border);
  border-radius: var(--radius);
  background: var(--callout-bg);
  color: var(--callout-text);
  font-size: 13px;
  line-height: var(--callout-line);
}

.callout--dense { padding: 8px 10px; gap: 8px; font-size: 12px; }

.callout__icon {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  /* One text line tall — centres the glyph against the first line, whatever the size. */
  height: calc(1em * var(--callout-line));
  color: var(--callout-accent);
}
.callout__body { min-width: 0; }
.callout__title { display: block; margin-bottom: 2px; font-weight: 800; color: var(--callout-accent); }
.callout__text { overflow-wrap: anywhere; }

/* Tones are token-driven so the component follows the theme; `info` borrows the brand accent
   rather than a generic blue, matching StatusBadge's "accent means ours" reading. */
.callout--info {
  --callout-bg: var(--surface-hi);
  --callout-border: var(--border-soft);
  --callout-text: var(--text-muted);
  --callout-accent: var(--accent);
}
.callout--muted {
  --callout-bg: var(--surface-hi);
  --callout-border: var(--border-soft);
  --callout-text: var(--text-muted);
  --callout-accent: var(--text-muted);
}
.callout--warn {
  --callout-bg: #fff4d1;
  --callout-border: #e2c76f;
  --callout-text: #71500d;
  --callout-accent: #71500d;
}
.callout--error {
  --callout-bg: #fff1ec;
  --callout-border: #efc7bf;
  --callout-text: #9f2f22;
  --callout-accent: #9f2f22;
}
</style>
