<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { IconCopy, IconCheck, IconListNumbers, IconCode } from '@tabler/icons-vue'
import { useHighlighter } from '@/composables/useHighlighter'

const props = defineProps<{
  code: string
  lang?: string
  showLineNumbers?: boolean
  /** icon — lang badge + icon buttons (default); accent — lang badge + primary copy button; minimal — no header, no copy */
  variant?: 'minimal' | 'icon' | 'accent'
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
  <div class="code-block">

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

    <!-- variant: minimal — no header -->

    <div
      class="code-block__body"
      :class="{ 'code-block__body--line-numbers': lineNumbers }"
      v-html="html"
    />
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

.code-block__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--surface-hi);
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

.code-block__btn:hover {
  background: var(--surface);
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

/* Reset global `code` styles that bleed green color/border/padding */
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

/* Override Shiki's pre/code defaults to match our theme */
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
