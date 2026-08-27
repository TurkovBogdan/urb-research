import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getNote, renameNote, type NoteDetail } from '../api'

// Деталка заметки: тип + скан + тело (markdown).
export const useNoteDetailStore = defineStore('research-note-detail', () => {
  const note = ref<NoteDetail | null>(null)
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

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
      error.value = e
      note.value = null
    } finally {
      if (current === code) loading.value = false
    }
  }

  // Отказ переименования гасится здесь: клиент уже показал тост, а вся оставшаяся реакция — не
  // менять название, отчего правка остаётся открытой с набранным текстом (её закрывает приход
  // НОВОГО названия). Поле `error` не трогаем — оно про отказ чтения раздела.
  const renaming = ref(false)

  async function rename(title: string) {
    const code = note.value?.code
    if (!code) return
    renaming.value = true
    try {
      note.value = await renameNote(code, title)
    } catch {
      // см. выше
    } finally {
      renaming.value = false
    }
  }

  function reset() {
    note.value = null
    error.value = null
  }

  return { note, loading, error, renaming, load, rename, reset }
})
