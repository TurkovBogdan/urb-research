import { defineStore } from 'pinia'
import { reactive } from 'vue'

import { persisted, strCodec } from '@/shared/utils/persisted'

// Состояние интерфейсов: то, в каком виде человек оставил список, когда ушёл с него.
//
// Отдельный дом от `settings`: там ВЫБОРЫ, которые настраивают однажды и правят на странице
// настроек, здесь — след работы, который человек не настраивал, а просто оставил. Держать порядок
// сортировки в сторе самого списка было мало: он живёт ровно до перезагрузки вкладки, и после неё
// список молча возвращался к своему умолчанию.
//
// Значения хранятся СТРОКАМИ и здесь не проверяются: набор ключей сортировки знает бэк каждого
// раздела, и его белый список живёт рядом с ним (`features/*/api.ts`). Стор списка сам чинит
// значение на чтении своим `resolve*` — тогда испорченный ключ в localStorage портит один список,
// а не запрос.
export const useUiStateStore = defineStore('ui-state', () => {
  // Умолчание реестра — «недавно обновлённые сверху», а не «когда завели»: открывая реестр,
  // возвращаются к тому, над чем работали, а не к тому, что однажды создали.
  const researchSort = reactive({
    by: persisted('ui.sort.researches.by', 'updated_at', strCodec),
    dir: persisted('ui.sort.researches.dir', 'desc', strCodec),
  })

  const groupSort = reactive({
    by: persisted('ui.sort.groups.by', 'research_updated_at', strCodec),
    dir: persisted('ui.sort.groups.dir', 'desc', strCodec),
  })

  return { researchSort, groupSort }
})
