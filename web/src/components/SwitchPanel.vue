<script setup lang="ts">
import { computed } from 'vue'

// Серая плашка-переключатель: VSwitch слева, заголовок + описание справа.
// Кликается целиком (сам VSwitch презентационный, pointer-events отключены —
// единственный путь переключения это toggle на контейнере).
// Текст можно задать общий (title/description) или раздельный для включённого
// (titleOn/descriptionOn) и выключенного (titleOff/descriptionOff) состояния —
// раздельный имеет приоритет, общий служит запасным.
// `tone` красит фон плашки и (по умолчанию) переключатель; `switchTone` красит
// только переключатель отдельно — например серая плашка с красным переключателем.
// `tone="transparent"` убирает фон и обводку (плашка без оформления — для вложения
// в собственный контейнер, например VCard).
type Tone = 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error'
type PanelTone = Tone | 'transparent'

const model = defineModel<boolean>({ default: false })

const props = withDefaults(defineProps<{
  title?: string
  titleOn?: string
  titleOff?: string
  description?: string
  descriptionOn?: string
  descriptionOff?: string
  disabled?: boolean
  tone?: PanelTone
  switchTone?: Tone
}>(), {
  tone: 'default',
})

const SWITCH_COLOR: Record<Tone, string> = {
  default: 'primary',
  primary: 'primary',
  info: 'info',
  success: 'success',
  warning: 'warning',
  error: 'error',
}
const effectiveSwitchTone = computed<Tone>(() =>
  props.switchTone ?? (props.tone === 'transparent' ? 'default' : props.tone),
)
const switchColor = computed(() => SWITCH_COLOR[effectiveSwitchTone.value])

const currentTitle = computed(() =>
  (model.value ? props.titleOn : props.titleOff) ?? props.title,
)
const currentDescription = computed(() =>
  (model.value ? props.descriptionOn : props.descriptionOff) ?? props.description,
)

function toggle() {
  if (props.disabled) return
  model.value = !model.value
}
</script>

<template>
  <div
    class="switch-panel"
    :class="[
      `switch-panel--${tone}`,
      `switch-panel--switch-${effectiveSwitchTone}`,
      { 'switch-panel--on': model, 'switch-panel--disabled': disabled },
    ]"
    role="switch"
    :aria-checked="model"
    :tabindex="disabled ? -1 : 0"
    @click="toggle"
    @keydown.enter.prevent="toggle"
    @keydown.space.prevent="toggle"
  >
    <VSwitch
      :model-value="model"
      :color="switchColor"
      :disabled="disabled"
      density="compact"
      hide-details
      inset
      readonly
      class="switch-panel__switch"
    />
    <div class="switch-panel__text">
      <div v-if="currentTitle" class="switch-panel__title">{{ currentTitle }}</div>
      <div class="switch-panel__desc">
        <slot>{{ currentDescription }}</slot>
      </div>
    </div>
  </div>
</template>

<style scoped>
.switch-panel {
  --sp-bg: color-mix(in srgb, var(--surface-hi) 50%, var(--surface));
  --sp-bg-hover: var(--surface-hi);
  --sp-border: color-mix(in srgb, var(--border-soft) 60%, var(--surface));
  --sp-switch-on: rgb(var(--v-theme-primary));

  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 7px 14px;
  background: var(--sp-bg);
  border: 1px solid var(--sp-border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.15s ease;
}

.switch-panel:hover { background: var(--sp-bg-hover); }

.switch-panel--primary {
  --sp-bg: var(--accent-soft);
  --sp-bg-hover: color-mix(in srgb, var(--accent-soft) 90%, var(--accent));
  --sp-border: color-mix(in srgb, var(--accent) 40%, var(--border-soft));
}

.switch-panel--info {
  --sp-bg: var(--info-soft);
  --sp-bg-hover: color-mix(in srgb, var(--info-soft) 90%, var(--info));
  --sp-border: color-mix(in srgb, var(--info) 40%, var(--border-soft));
}

.switch-panel--success {
  --sp-bg: var(--success-soft);
  --sp-bg-hover: color-mix(in srgb, var(--success-soft) 90%, var(--success));
  --sp-border: color-mix(in srgb, var(--success) 40%, var(--border-soft));
}

.switch-panel--warning {
  --sp-bg: var(--warn-soft);
  --sp-bg-hover: color-mix(in srgb, var(--warn-soft) 90%, var(--warn));
  --sp-border: color-mix(in srgb, var(--warn) 40%, var(--border-soft));
}

.switch-panel--error {
  --sp-bg: var(--error-soft);
  --sp-bg-hover: color-mix(in srgb, var(--error-soft) 90%, var(--error));
  --sp-border: color-mix(in srgb, var(--error) 40%, var(--border-soft));
}

/* No chrome — bare switch + text, meant to sit inside a host container (e.g. VCard). */
.switch-panel--transparent {
  --sp-bg: transparent;
  --sp-bg-hover: transparent;
  --sp-border: transparent;
  padding: 0;
}

/* Switch track colour — set independently of the panel tone so a grey panel can
   carry a coloured (e.g. red) switch. switchTone falls back to tone in the script. */
.switch-panel--switch-primary { --sp-switch-on: rgb(var(--v-theme-primary)); }
.switch-panel--switch-info    { --sp-switch-on: rgb(var(--v-theme-info)); }
.switch-panel--switch-success { --sp-switch-on: rgb(var(--v-theme-success)); }
.switch-panel--switch-warning { --sp-switch-on: rgb(var(--v-theme-warning)); }
.switch-panel--switch-error   { --sp-switch-on: rgb(var(--v-theme-error)); }

/* The global rule (main.scss) paints every checked track with --accent;
   re-tint it per switch tone — scoped :deep wins on specificity. */
.switch-panel :deep(.v-switch:has(input:checked) .v-switch__track) {
  background: var(--sp-switch-on);
}

.switch-panel:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.switch-panel--disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.switch-panel__switch {
  flex: 0 0 auto;
  margin: 0;
  pointer-events: none;
}

.switch-panel__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.switch-panel__title {
  font-size: 13px;
  color: var(--text);
  line-height: 1.3;
}

.switch-panel__desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}
</style>
