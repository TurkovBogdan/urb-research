import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getQuery, type QueryDetail } from '../api'

// Детальная запроса: сам запрос + его выдача (строки результата с полями страницы).
export const useQueryDetailStore = defineStore('web_search-query-detail', () => {
  const query = ref<QueryDetail | null>(null)
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

  const results = computed(() => query.value?.results ?? [])

  async function load(code: string) {
    loading.value = true
    error.value = null
    try {
      query.value = await getQuery(code)
    } catch (e) {
      error.value = e
      query.value = null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    query.value = null
    error.value = null
  }

  return { query, results, loading, error, load, reset }
})
