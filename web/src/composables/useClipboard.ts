import { onUnmounted, ref, type Ref } from 'vue'

/**
 * Копирование в буфер с самоочищающейся отметкой «скопировано» — то, что нужно любой кнопке копии.
 *
 * Отметка держит САМ СКОПИРОВАННЫЙ ТЕКСТ, а не флаг: в списке кнопок булев флаг зажёгся бы разом
 * на всех строках. Кнопке с единственной целью хватает `isCopied(своё значение)`.
 *
 * Запасной путь через textarea — не перестраховка: под Qt WebEngine асинхронный clipboard-API
 * отклоняет запись, пока документ не в фокусе.
 */
export function useClipboard(resetAfter = 1800): {
  copiedText: Ref<string | null>
  copy: (text: string) => Promise<void>
  isCopied: (text: string) => boolean
} {
  const copiedText = ref<string | null>(null)
  let timer: ReturnType<typeof setTimeout> | undefined

  function writeViaHiddenTextarea(text: string): void {
    const el = document.createElement('textarea')
    el.value = text
    el.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0'
    document.body.appendChild(el)
    el.focus()
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }

  async function copy(text: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      writeViaHiddenTextarea(text)
    }

    copiedText.value = text
    clearTimeout(timer)
    timer = setTimeout(() => { copiedText.value = null }, resetAfter)
  }

  const isCopied = (text: string): boolean => copiedText.value === text

  // Иначе таймер добежит до размонтированного компонента и Vue отругается на запись в ref.
  onUnmounted(() => clearTimeout(timer))

  return { copiedText, copy, isCopied }
}
