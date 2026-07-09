import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getPage, type WebSearchPageDetail } from '../api'

// Детальная страницы: метаданные + markdown-контент.
export const usePageDetailStore = defineStore('web_search-page-detail', () => {
  const page = ref<WebSearchPageDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load(code: string) {
    loading.value = true
    error.value = null
    try {
      page.value = await getPage(code)
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      page.value = null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    page.value = null
    error.value = null
  }

  return { page, loading, error, load, reset }
})
