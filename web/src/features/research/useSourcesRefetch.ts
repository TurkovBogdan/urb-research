// Повтор получения материала источника — обвязка раздела «Источники».
//
// Композабл, а не стор: своих данных у действия нет, оно правит чужие. После прогона страница
// перечитывает источники целиком, а не патчит ответом: страница дедуплицирована между
// исследованиями, поэтому ожившая страница могла снять ошибку и с тех строк, которых мы не
// просили. Сообщение — единственный след действия: строки, оставшиеся без материала, выглядят
// ровно так же, как до нажатия, и молчание читалось бы как «ничего не произошло».
//
// Чинят по одной строке: «перекачать всё сломанное» — долгий прогон, по итогу которого не видно,
// что именно чинили, и раздел один и тот же на исследовании и на зоне.
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { pushToast } from '@/composables/useToasts'

import { refetchSourceDocument, type SourceDocumentRow } from './api'

/** @param reload Перечитать источники раздела. */
export function useSourcesRefetch(reload: () => unknown) {
  const { t } = useI18n()

  // Код, а не флаг: по нему видно, какая именно строка сейчас качается, и запирается она одна.
  const refetchingCode = ref<string | null>(null)

  // Итог читается по новому статусу строки: `error` — материала снова нет.
  function report(row: SourceDocumentRow) {
    if (row.status === 'error') pushToast(t('research.doc.refetch.failed'), 'warn')
    else pushToast(t('research.doc.refetch.done'), 'success')
  }

  async function refetchOneSource(code: string) {
    if (refetchingCode.value) return
    refetchingCode.value = code
    try {
      report(await refetchSourceDocument(code))
      await reload()
    } catch {
      // Отказ уже показан тостом клиента API, а вся оставшаяся реакция — оставить раздел как был.
    } finally {
      refetchingCode.value = null
    }
  }

  return { refetchingCode, refetchOneSource }
}
