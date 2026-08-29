import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getSourceDocument, type SourceDocumentDetail } from '../api'
import { matchesQuery, normalizeQuery } from '../search'

// Деталка источника по коду (цель ссылки SOURCE@<code> из тела исследования).
export const useSourceDetailStore = defineStore('research-source-detail', () => {
  const source = ref<SourceDocumentDetail | null>(null)
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

  // ── Поиск по деталке ────────────────────────────────────────────────────────
  // Материал источника целиком на клиенте, поэтому ищем сами — как на зоне и заметке.
  const search = ref('')
  const needle = computed(() => normalizeQuery(search.value))
  const searching = computed(() => needle.value.length > 0)

  // Карточка источника — имя, адрес и разбор: чем он оказался полезен и что с ним не так.
  const briefMatches = computed(() =>
    matchesQuery(
      [source.value?.title, source.value?.url, source.value?.summary, source.value?.note],
      needle.value,
    ),
  )
  const bodyMatches = computed(() => matchesQuery([source.value?.body], needle.value))

  const matchCount = computed(() => Number(briefMatches.value) + Number(bodyMatches.value))

  let current = ''

  async function load(code: string) {
    // Запрос переживает обновление той же страницы, но не переход на другой источник: унесённая
    // строка искала бы в чужих данных.
    if (code !== current) search.value = ''
    current = code
    loading.value = true
    error.value = null
    try {
      const data = await getSourceDocument(code)
      if (current !== code) return
      source.value = data
    } catch (e) {
      if (current !== code) return
      error.value = e
      source.value = null
    } finally {
      if (current === code) loading.value = false
    }
  }

  function reset() {
    source.value = null
    search.value = ''
    error.value = null
  }

  return {
    source, loading, error,
    search, searching, briefMatches, bodyMatches, matchCount,
    load, reset,
  }
})
