// Повтор получения материала источников — общая обвязка страниц исследования и зоны.
//
// Композабл, а не стор: своих данных у действия нет, оно правит чужие. После прогона страница
// перечитывает источники целиком, а не патчит ответом: страница дедуплицирована между
// исследованиями, поэтому ожившая страница могла снять ошибку и с тех строк, которых мы не
// просили. Сообщение — единственный след действия: строки, оставшиеся без материала, выглядят
// ровно так же, как до нажатия, и молчание читалось бы как «ничего не произошло».
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { pushToast } from '@/composables/useToasts'

import { refetchSourceDocument, type SourceDocumentRow } from './api'

/**
 * @param refetchAll Перекачать всё сломанное в текущем разделе (уровень выбирает страница).
 * @param reload Перечитать источники раздела.
 */
export function useSourcesRefetch(
  refetchAll: () => Promise<SourceDocumentRow[]>,
  reload: () => unknown,
) {
  const { t } = useI18n()

  // Два признака занятости, а не один: кнопка и пункт строки блокируются каждый сам по себе,
  // и по коду видно, какая именно строка сейчас качается.
  const refetchingAll = ref(false)
  const refetchingCode = ref<string | null>(null)

  function report(rows: SourceDocumentRow[]) {
    const arrived = rows.filter((row) => row.status !== 'error').length
    if (rows.length === 0) {
      pushToast(t('research.doc.refetch.nothing'), 'info')
    } else if (arrived === rows.length) {
      pushToast(t('research.doc.refetch.done'), 'success')
    } else if (arrived === 0) {
      pushToast(t('research.doc.refetch.failed'), 'warn')
    } else {
      pushToast(t('research.doc.refetch.partial', { arrived, total: rows.length }), 'warn')
    }
  }

  async function run(action: () => Promise<SourceDocumentRow[]>) {
    try {
      report(await action())
      await reload()
    } catch {
      // Отказ уже показан тостом клиента API, а вся оставшаяся реакция — оставить раздел как был.
    }
  }

  async function refetchAllSources() {
    if (refetchingAll.value) return
    refetchingAll.value = true
    try {
      await run(refetchAll)
    } finally {
      refetchingAll.value = false
    }
  }

  async function refetchOneSource(code: string) {
    if (refetchingCode.value) return
    refetchingCode.value = code
    try {
      await run(async () => [await refetchSourceDocument(code)])
    } finally {
      refetchingCode.value = null
    }
  }

  return { refetchingAll, refetchingCode, refetchAllSources, refetchOneSource }
}
