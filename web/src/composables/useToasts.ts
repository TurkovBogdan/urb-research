import { readonly, ref } from 'vue'

// Всплывающие сообщения. Заведено под одно правило: отказ, который экран не показал сам,
// обязан всплыть здесь. Молчание должно требовать явного действия, а не получаться само.
//
// Модуль, а не Pinia: сюда пишет клиент API, то есть код вне компонентов.

/** Уровень = тон палитры. Имена совпадают со словарём токенов, включая `warn`. */
export type ToastLevel = 'success' | 'info' | 'warn' | 'error'

export interface Toast {
  id: number
  text: string
  level: ToastLevel
  /** Через сколько миллисекунд снять; 0 — держать до закрытия человеком. */
  timeout: number
}

/** Сколько живёт сообщение. Один срок на все уровни: его же отсчитывает кольцо у крестика. */
const DEFAULT_TIMEOUT = 5000

/**
 * Потолок очереди. Показ идёт по одному, и без потолка десятый отказ дождался бы своей очереди
 * через сорок пять секунд — когда он уже никому не нужен. Вытесняем САМЫЕ СТАРЫЕ: свежий отказ
 * ближе к тому, что человек делает сейчас.
 */
const MAX_QUEUED = 3

const items = ref<Toast[]>([])
let lastId = 0

export const toasts = readonly(items)

/**
 * Показать сообщение. Повтор той же пары «текст + уровень» игнорируется, пока прежний висит:
 * пять параллельных запросов, упавших одинаково, — это одна новость, а не пять. Уровень входит
 * в ключ намеренно: один и тот же текст успехом и ошибкой — разные новости.
 */
export function pushToast(text: string, level: ToastLevel = 'error', timeout = DEFAULT_TIMEOUT): void {
  const message = text.trim()
  if (message === '') {
    return
  }

  for (const toast of items.value) {
    if (toast.text === message && toast.level === level) {
      return
    }
  }

  lastId += 1

  const next = [...items.value, { id: lastId, text: message, level, timeout }]
  items.value = next.length > MAX_QUEUED ? next.slice(next.length - MAX_QUEUED) : next
}

export function dismissToast(id: number): void {
  items.value = items.value.filter(toast => toast.id !== id)
}

export function clearToasts(): void {
  items.value = []
}
