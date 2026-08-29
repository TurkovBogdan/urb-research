// Что показывает колонка деталки — и кто это ей говорит.
//
// Сама колонка живёт в `DetailShell` и переживает переходы между деталками: при уходе на другой
// артефакт меняется только содержимое справа, а плашка выхода, поиск и оглавление перестраиваются
// на месте, не мигая. Значит, страница не рисует колонку, а ЗАПОЛНЯЕТ её — через этот реестр.
//
// Строку поиска реестр не хранит: она принадлежит стору страницы (по ней же идёт фильтрация её
// разделов), поэтому сюда приходит пара «текущее значение + как его записать».
import { onActivated, onDeactivated, onMounted, onUnmounted, ref, shallowRef, watchEffect } from 'vue'

import type { NavSection } from '@/components/SectionNav.vue'

export interface DetailRailSearch {
  label: string
  value: string
  update: (query: string) => void
  /** «Найдено элементов: N» — пусто, когда не ищут. */
  summary: string
  /** Подпись догоняющей половины поиска («ищу в текстах…») — пусто, когда искать больше негде.
      Пока она есть, счётчик рядом промежуточный, и колесо рядом с ней об этом говорит. */
  pending?: string
}

export interface DetailRailConfig {
  /** Запасной адрес выхода: ближайший родитель в дереве. */
  parent: string
  /** Имя запасного места — стоит на кнопке при заходе по прямой ссылке. */
  label: string
  /** Страница показывает документ: в строке выхода появляется шестерёнка оформления. */
  appearance?: boolean
  sections?: NavSection[]
  search?: DetailRailSearch
}

const config = shallowRef<DetailRailConfig | null>(null)

/** Читает колонка. */
export function detailRail() {
  return config
}

/**
 * Заполняет страница. Собранное значение пересчитывается само, пока страница на экране.
 *
 * Сверка с экраном обязательна: `KeepAlive` не размонтирует ушедшую вьюху, и её эффект
 * продолжал бы переписывать колонку данными чужой страницы поверх пришедшей.
 */
export function useDetailRail(build: () => DetailRailConfig): void {
  const onScreen = ref(false)

  onMounted(() => { onScreen.value = true })
  onActivated(() => { onScreen.value = true })
  onDeactivated(() => { onScreen.value = false })
  onUnmounted(() => { onScreen.value = false })

  watchEffect(() => {
    if (onScreen.value) config.value = build()
  })
}
