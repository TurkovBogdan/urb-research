<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { IconCopy, IconCheck, IconListNumbers, IconCode } from '@tabler/icons-vue'
import { useHighlighter } from '@/composables/useHighlighter'

const props = defineProps<{
  code: string
  lang?: string
  showLineNumbers?: boolean
  /** icon — lang badge + icon buttons (default); accent — lang badge + primary copy button;
   *  minimal — no header, no copy; compact — one-liner: no header, copy button on hover */
  variant?: 'minimal' | 'icon' | 'accent' | 'compact'
}>()

const { highlight } = useHighlighter()

const html = ref('')
const lineNumbers = ref(props.showLineNumbers ?? false)
const copied = ref(false)

async function render() {
  html.value = await highlight(props.code, props.lang ?? 'text')
}

onMounted(render)
watch(() => [props.code, props.lang], render)
watch(() => props.showLineNumbers, (v) => { lineNumbers.value = v ?? false })

function toggleLineNumbers() {
  lineNumbers.value = !lineNumbers.value
}

async function copy() {
  try {
    await navigator.clipboard.writeText(props.code)
  } catch {
    // Fallback for Qt WebEngine where clipboard API requires document focus
    const el = document.createElement('textarea')
    el.value = props.code
    el.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0'
    document.body.appendChild(el)
    el.focus()
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 1800)
}

const resolvedVariant = () => props.variant ?? 'icon'
</script>

<template>
  <div class="code-block" :class="{ 'code-block--compact': resolvedVariant() === 'compact' }">

    <!-- variant: icon — lang badge + icon buttons -->
    <div v-if="resolvedVariant() === 'icon'" class="code-block__header">
      <span class="code-block__lang">
        <IconCode :size="13" stroke-width="2" />
        {{ lang ?? 'text' }}
      </span>
      <div class="code-block__actions">
        <button
          class="code-block__btn"
          :class="{ 'code-block__btn--active': lineNumbers }"
          title="Номера строк"
          @click="toggleLineNumbers"
        >
          <IconListNumbers :size="14" stroke-width="2" />
        </button>
        <button
          class="code-block__btn"
          :class="{ 'code-block__btn--copied': copied }"
          title="Скопировать"
          @click="copy"
        >
          <IconCheck v-if="copied" :size="14" stroke-width="2.5" />
          <IconCopy v-else :size="14" stroke-width="2" />
        </button>
      </div>
    </div>

    <!-- variant: accent — lang badge + primary copy button -->
    <div v-else-if="resolvedVariant() === 'accent'" class="code-block__header">
      <span class="code-block__lang">
        <IconCode :size="13" stroke-width="2" />
        {{ lang ?? 'text' }}
      </span>
      <VBtn
        color="primary"
        variant="flat"
        size="x-small"
        :prepend-icon="copied ? IconCheck : IconCopy"
        @click="copy"
      >
        {{ copied ? 'Скопировано' : 'Копировать' }}
      </VBtn>
    </div>

    <!-- variant: minimal — no header; compact — no header, the copy button floats over the code -->

    <div
      class="code-block__body"
      :class="{ 'code-block__body--line-numbers': lineNumbers }"
      v-html="html"
    />

    <button
      v-if="resolvedVariant() === 'compact'"
      class="code-block__btn code-block__copy-float"
      :class="{ 'code-block__btn--copied': copied }"
      title="Скопировать"
      @click="copy"
    >
      <IconCheck v-if="copied" :size="13" stroke-width="2.5" />
      <IconCopy v-else :size="13" stroke-width="2" />
    </button>
  </div>
</template>

<style scoped>
.code-block {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: 12px;
}

/* The header shares the panel's surface instead of sitting a step above it: on a light card
   the body is white and a raised header was the only filled area, so the block read as a grey
   cap with nothing under it. The rule below it is what separates the two. */
.code-block__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--surface);
  border-bottom: 1px solid var(--border-soft);
  user-select: none;
}

.code-block__lang {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-mono);
  text-transform: lowercase;
}

.code-block__actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.code-block__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-faint);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

/* One step up from the header, which now shares the panel surface — the old value matched it
   and the hover state was invisible. */
.code-block__btn:hover {
  background: var(--surface-hi);
  color: var(--text-muted);
}

.code-block__btn--active {
  color: var(--accent);
}

.code-block__btn--active:hover {
  color: var(--accent);
}

.code-block__btn--copied {
  color: var(--accent);
}

.code-block__body {
  overflow-x: auto;
}

/* Compact: a one-liner reads as a command chip, not as a code panel — no header, tighter
   padding, and the copy button appears over the right edge on hover. */
.code-block--compact {
  position: relative;
}

.code-block--compact .code-block__body :deep(pre) {
  padding: 6px 10px;
}

.code-block__copy-float {
  position: absolute;
  top: 50%;
  right: 4px;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  background: var(--surface-hi);
  opacity: 0;
  transition: opacity 0.12s, background 0.12s, color 0.12s;
}

.code-block--compact:hover .code-block__copy-float,
.code-block__copy-float:focus-visible {
  opacity: 1;
}

/* Reset the global `code` chip (accent colour, border, padding) that main.scss paints on every
   bare `code` — inside a highlighted panel it would draw a box around the whole listing. */
.code-block__body :deep(code) {
  background: transparent !important;
  color: inherit !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
}

/* Strip any token-level backgrounds the theme may inject */
.code-block__body :deep(span) {
  background: transparent !important;
}

/* Override Shiki's pre/code defaults to match our theme. The plate is the app's own surface
   rather than the syntax theme's: it has to sit inside a card next to other blocks, and two
   competing greys would read as a seam. Only the token colours come from the theme. */
.code-block__body :deep(pre) {
  margin: 0;
  padding: 12px 14px;
  background: var(--surface) !important;
  border-radius: 0;
  border: none;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.65;
}

/* Each token carries both palettes as custom properties (see composables/useHighlighter.ts);
   these two rules are what picks one. Dark is the unconditional branch and light is the
   override, mirroring how the colour tokens are declared in styles/main.scss — so a frame
   rendered before the store has written `data-theme` still pairs dark tokens with the dark
   surface it is sitting on. */
.code-block__body :deep(pre),
.code-block__body :deep(pre span) {
  color: var(--shiki-dark);
}

html[data-theme='light'] .code-block__body :deep(pre),
html[data-theme='light'] .code-block__body :deep(pre span) {
  color: var(--shiki-light);
}

/* Line numbers via CSS counter */
.code-block__body--line-numbers :deep(.line) {
  counter-increment: line-num;
}

.code-block__body--line-numbers :deep(pre) {
  counter-reset: line-num;
  padding-left: 0;
}

.code-block__body--line-numbers :deep(.line)::before {
  content: counter(line-num);
  display: inline-block;
  width: 2.2em;
  margin-right: 1.2em;
  text-align: right;
  color: var(--text-faint);
  user-select: none;
  flex-shrink: 0;
}
</style>
