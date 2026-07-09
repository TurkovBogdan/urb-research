import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getResearch, type ResearchDetail } from '../api'

// Деталка исследования: тело + области, поиски и заметки (скан-слой).
export const useResearchDetailStore = defineStore('research-research-detail', () => {
  const research = ref<ResearchDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const areas = computed(() => research.value?.areas ?? [])
  const queries = computed(() => research.value?.queries ?? [])
  const notes = computed(() => research.value?.notes ?? [])

  // Latest-navigation-wins: a slower earlier response for a stale code is dropped, so
  // rapid page-to-page navigation always settles on the current route's data.
  let current = ''

  async function load(code: string) {
    current = code
    loading.value = true
    error.value = null
    try {
      const data = await getResearch(code)
      if (current !== code) return
      research.value = data
    } catch (e) {
      if (current !== code) return
      error.value = e instanceof Error ? e.message : String(e)
      research.value = null
    } finally {
      if (current === code) loading.value = false
    }
  }

  function reset() {
    research.value = null
    error.value = null
  }

  return { research, areas, queries, notes, loading, error, load, reset }
})
