import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getSourceDocument, type SourceDocumentDetail } from '../api'

// Деталка источника по коду (цель ссылки SOURCE@<code> из тела исследования).
export const useSourceDetailStore = defineStore('research-source-detail', () => {
  const source = ref<SourceDocumentDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let current = ''

  async function load(code: string) {
    current = code
    loading.value = true
    error.value = null
    try {
      const data = await getSourceDocument(code)
      if (current !== code) return
      source.value = data
    } catch (e) {
      if (current !== code) return
      error.value = e instanceof Error ? e.message : String(e)
      source.value = null
    } finally {
      if (current === code) loading.value = false
    }
  }

  function reset() {
    source.value = null
    error.value = null
  }

  return { source, loading, error, load, reset }
})
