<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  IconAlertCircle, IconAlertTriangle, IconCheck, IconInfoCircle, IconX, type Icon,
} from '@tabler/icons-vue'
import { dismissToast, toasts, type ToastLevel } from '@/composables/useToasts'

// Показ всплывающих сообщений: по одному, снизу справа, поверх всего. Очередь держит
// `useToasts`, здесь показ и отсчёт до автозакрытия.
//
// Цвет берётся ТОКЕНАМИ палитры, а не палитрой Vuetify (`color="error"` красит сплошным):
// мягкая заливка, рамка из того же тона, текст обычный, тоном окрашена только иконка. Светлая
// тема достаётся даром, токены в ней уже переопределены.
//
// Срок отсчитываем сами, а не `:timeout` у VSnackbar: то же время рисует кольцо у крестика, и
// два владельца одного срока разошлись бы. Наведение отсчёт ДЕРЖИТ — иначе сообщение исчезает
// из-под курсора, который тянулся его закрыть.
//
// ⚠️ Остаток считается от ОТМЕТКИ ВРЕМЕНИ, а не вычитанием шага: в фоновой вкладке браузер
// душит таймеры до одного тика в секунду, и вычитание растянуло бы пять секунд на пятьдесят,
// заперев очередь.

const icons: Record<ToastLevel, Icon> = {
  success: IconCheck,
  info: IconInfoCircle,
  warn: IconAlertTriangle,
  error: IconAlertCircle,
}

/** Шаг отсчёта: кольцо должно таять плавно, а не прыгать раз в секунду. */
const TICK_MS = 100

// Показываем самое старое: пришедшие следом ждут своей очереди, а не перекрывают его.
const current = computed(() => toasts.value[0] ?? null)

const left = ref(0)
// Две РАЗНЫЕ вещи: `paused` — курсор где угодно на сообщении (читают текст, срок держим);
// `overClose` — курсор или фокус на самой кнопке (там кольцо уступает место крестику).
const paused = ref(false)
const overClose = ref(false)
let ticker: ReturnType<typeof setInterval> | undefined
let deadlineAt = 0

/** Целые секунды в кольце: 5-4-3-2-1. */
const seconds = computed(() => Math.ceil(left.value / 1000))
const percent = computed(() => {
  const total = current.value?.timeout ?? 0

  return total > 0 ? (left.value / total) * 100 : 0
})

// Сообщение без срока (`timeout: 0`) висит до закрытия — там кольцу нечего показывать.
const counting = computed(() => left.value > 0)

function stopTicker(): void {
  if (ticker !== undefined) {
    clearInterval(ticker)
    ticker = undefined
  }
}

watch(current, (toast) => {
  stopTicker()
  paused.value = false
  overClose.value = false
  left.value = toast?.timeout ?? 0

  if (toast === null || toast.timeout <= 0) {
    return
  }

  deadlineAt = Date.now() + toast.timeout

  ticker = setInterval(() => {
    // Пауза сдвигает срок вперёд ровно на прошедшее время, а не «замораживает» счётчик.
    if (paused.value) {
      deadlineAt = Date.now() + left.value

      return
    }

    left.value = Math.max(0, deadlineAt - Date.now())

    if (left.value === 0) {
      stopTicker()
      dismissToast(toast.id)
    }
  }, TICK_MS)
}, { immediate: true })

onBeforeUnmount(stopTicker)
</script>

<template>
  <VSnackbar
    v-if="current"
    :key="current.id"
    :model-value="true"
    :timeout="-1"
    location="bottom right"
    class="toast"
    :class="`toast--${current.level}`"
  >
    <div
      class="toast__body"
      @mouseenter="paused = true"
      @mouseleave="paused = false"
    >
      <component :is="icons[current.level]" :size="18" class="toast__icon" />
      <span>{{ current.text }}</span>
    </div>

    <template #actions>
      <!-- Кнопка есть ВСЕГДА: она и фокусируемая цель для клавиатуры, и место под отсчёт.
           Меняется только её содержимое — кольцо в покое, крестик под курсором и под фокусом,
           поэтому вёрстка не двигается. -->
      <button
        type="button"
        class="toast__close"
        :aria-label="$t('common.action.close')"
        @mouseenter="paused = true; overClose = true"
        @mouseleave="paused = false; overClose = false"
        @focus="paused = true; overClose = true"
        @blur="paused = false; overClose = false"
        @click="dismissToast(current.id)"
      >
        <VProgressCircular
          v-if="counting && !overClose"
          :model-value="percent"
          :size="28"
          :width="2"
          class="toast__count"
        >
          {{ seconds }}
        </VProgressCircular>

        <IconX v-else :size="16" />
      </button>
    </template>
  </VSnackbar>
</template>

<style scoped>
.toast--success { --toast-accent: var(--success); --toast-bg: var(--success-soft); }
.toast--info    { --toast-accent: var(--info);    --toast-bg: var(--info-soft); }
.toast--warn    { --toast-accent: var(--warn);    --toast-bg: var(--warn-soft); }
.toast--error   { --toast-accent: var(--error);   --toast-bg: var(--error-soft); }

/* Полотно рисует сам Vuetify, поэтому тон кладём на его обёртку. Текст обычный, а не в цвет
   тона: мягкая заливка + цветная строка дают контраст ниже читаемого. */
.toast :deep(.v-snackbar__wrapper) {
  background: var(--toast-bg);
  color: var(--text);
  border: 1px solid color-mix(in srgb, var(--toast-accent) 32%, transparent);
  border-radius: var(--radius);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
}

.toast__body {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toast__icon {
  flex: none;
  color: var(--toast-accent);
}

.toast__count {
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* Кольцо целиком в тоне сообщения. ⚠️ `!important` тут не украшение: глобальные правила в
   `styles/main.scss` красят ЛЮБОЙ `v-progress-circular` акцентом, а его дорожку —
   `--border-soft`, и оба объявлены важными. Локально перебить их можно только так. */
.toast :deep(.toast__count) {
  color: var(--toast-accent) !important;
}
.toast :deep(.v-progress-circular__overlay) {
  stroke: var(--toast-accent);
}
.toast :deep(.v-progress-circular__underlay) {
  stroke: color-mix(in srgb, var(--toast-accent) 20%, transparent) !important;
}

/* Размер держит кнопка, а не содержимое: кольцо и крестик меняются в одной коробке 28×28,
   поэтому полотно не дёргается. */
.toast__close {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
}
.toast__close:hover {
  color: var(--toast-accent);
  background: color-mix(in srgb, var(--toast-accent) 12%, transparent);
}
.toast__close:focus-visible {
  outline: 2px solid var(--toast-accent);
  outline-offset: 1px;
}
</style>
