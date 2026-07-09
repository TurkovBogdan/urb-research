<script setup lang="ts">
import { computed } from 'vue'
import { IconChevronRight } from '@tabler/icons-vue'

// Сворачиваемая секция: кликабельная шапка (заголовок + шеврон) над раскрываемым
// содержимым. Раскрытие — VExpandTransition (плавная высота). Состояние через
// v-model:boolean (необязательное, по умолчанию закрыт).
// `variant` задаёт тему оформления: default — плашка с рамкой; minimal —
// безрамочная строка-заголовок; card — заливка surface-hi в шапке.
// `color`/`activeColor` переопределяют цвет шапки (заголовок + шеврон) в покое и
// при наведении — для отдельных интерфейсов; не заданы → цвета темы варианта.
type Variant = 'default' | 'minimal' | 'card'

const model = defineModel<boolean>({ default: false })

const props = withDefaults(defineProps<{
  title?: string
  variant?: Variant
  disabled?: boolean
  color?: string
  activeColor?: string
}>(), {
  variant: 'default',
})

const colorVars = computed(() => ({
  ...(props.color ? { '--spoiler-color': props.color } : {}),
  ...(props.activeColor ? { '--spoiler-active-color': props.activeColor } : {}),
}))

function toggle() {
  if (props.disabled) return
  model.value = !model.value
}
</script>

<template>
  <div
    class="spoiler"
    :class="[`spoiler--${variant}`, { 'spoiler--open': model, 'spoiler--disabled': disabled }]"
    :style="colorVars"
  >
    <button
      type="button"
      class="spoiler__head"
      :disabled="disabled"
      :aria-expanded="model"
      @click="toggle"
    >
      <IconChevronRight class="spoiler__chevron" :size="16" :stroke-width="2" />
      <span class="spoiler__title">
        <slot name="title">{{ title }}</slot>
      </span>
      <span v-if="$slots.actions" class="spoiler__actions" @click.stop>
        <slot name="actions" />
      </span>
    </button>

    <VExpandTransition>
      <div v-show="model" class="spoiler__body">
        <div class="spoiler__content">
          <slot />
        </div>
      </div>
    </VExpandTransition>
  </div>
</template>

<style scoped>
.spoiler {
  border-radius: var(--radius);
}

.spoiler__head {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--spoiler-color, var(--text));
  font: inherit;
  transition: background 0.15s ease, color 0.15s ease;
}

.spoiler__head:hover {
  color: var(--spoiler-active-color, var(--text));
}

.spoiler__chevron {
  flex: 0 0 auto;
  color: var(--spoiler-color, var(--text-faint));
  transition: transform 0.2s ease, color 0.15s ease;
}

.spoiler__head:hover .spoiler__chevron {
  color: var(--spoiler-active-color, var(--text-faint));
}

.spoiler--open .spoiler__chevron {
  transform: rotate(90deg);
}

.spoiler__title {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.3;
  transition: color 0.15s ease;
}

.spoiler__actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 4px;
}

.spoiler__content {
  padding: 0 14px 12px 36px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.spoiler__head:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
  border-radius: var(--radius);
}

.spoiler--disabled .spoiler__head {
  cursor: not-allowed;
  opacity: 0.6;
}

.spoiler--default {
  background: var(--surface);
  border: 1px solid var(--border-soft);
}

.spoiler--default .spoiler__head:hover {
  background: var(--surface-hi);
}

.spoiler--card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  overflow: hidden;
}

.spoiler--card .spoiler__head {
  background: var(--surface-hi);
}

.spoiler--card.spoiler--open .spoiler__head {
  border-bottom: 1px solid var(--border-soft);
}

.spoiler--card .spoiler__content {
  padding-top: 12px;
}

.spoiler--minimal .spoiler__head {
  padding: 4px 0;
  color: var(--spoiler-color, var(--text-faint));
}

.spoiler--minimal .spoiler__title {
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.spoiler--minimal .spoiler__head:hover,
.spoiler--minimal .spoiler__head:hover .spoiler__chevron {
  color: var(--spoiler-active-color, var(--text-muted));
}

.spoiler--minimal .spoiler__content {
  padding: 4px 0 8px 24px;
}
</style>
