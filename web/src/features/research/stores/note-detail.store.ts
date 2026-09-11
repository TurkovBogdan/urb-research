import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { editNoteDescription, getNote, renameNote, type NoteDetail } from '../api'
import { matchesQuery, normalizeQuery } from '../search'

// Деталка заметки: тип + скан + тело (markdown).
export const useNoteDetailStore = defineStore('research-note-detail', () => {
  const note = ref<NoteDetail | null>(null)
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

  // ── Поиск по деталке ────────────────────────────────────────────────────────
  // Как у зоны: всё, по чему ищут, уже на клиенте, поэтому за ответом бэкенда здесь не ходят.
  const search = ref('')
  const needle = computed(() => normalizeQuery(search.value))
  const searching = computed(() => needle.value.length > 0)

  const briefMatches = computed(() =>
    matchesQuery([note.value?.title, note.value?.description], needle.value),
  )
  const bodyMatches = computed(() => matchesQuery([note.value?.body], needle.value))

  const matchCount = computed(() => Number(briefMatches.value) + Number(bodyMatches.value))

  let current = ''

  async function load(code: string) {
    // Запрос переживает обновление той же страницы, но не переход на другую заметку: унесённая
    // строка искала бы в чужих данных.
    if (code !== current) search.value = ''
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

  // Правка описания живёт по тем же правилам, что и переименование: свой флаг «в полёте», отказ
  // гасится тостом клиента. Ответ — удалось или нет: правку закрывает владелец поля, и «текст
  // сохранён» он иначе не отличит от «текст сохранён тот же самый».
  const describing = ref(false)

  async function saveDescription(description: string): Promise<boolean> {
    const code = note.value?.code
    if (!code) return false
    describing.value = true
    try {
      note.value = await editNoteDescription(code, description)
      return true
    } catch {
      return false
    } finally {
      describing.value = false
    }
  }

  function reset() {
    note.value = null
    search.value = ''
    error.value = null
  }

  return {
    note, loading, error, renaming, describing,
    search, searching, briefMatches, bodyMatches, matchCount,
    load, rename, saveDescription, reset,
  }
})
