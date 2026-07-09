import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getNote, type NoteDetail } from '../api'

// Деталка заметки: тип + скан + тело (markdown).
export const useNoteDetailStore = defineStore('research-note-detail', () => {
  const note = ref<NoteDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let current = ''

  async function load(code: string) {
    current = code
    loading.value = true
    error.value = null
    try {
      const data = await getNote(code)
      if (current !== code) return
      note.value = data
    } catch (e) {
      if (current !== code) return
      error.value = e instanceof Error ? e.message : String(e)
      note.value = null
    } finally {
      if (current === code) loading.value = false
    }
  }

  function reset() {
    note.value = null
    error.value = null
  }

  return { note, loading, error, load, reset }
})
