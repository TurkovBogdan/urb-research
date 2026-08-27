import { bundledLanguages, createHighlighter, type BundledLanguage, type Highlighter } from 'shiki'

// One highlighter for the app. Languages are loaded on demand instead of up front, and a fence
// language is resolved against shiki's own bundle — it already knows the aliases (`js`, `sh`,
// `yml`, `py`), so a local whitelist would only narrow what shiki supports.
//
// Both schemes are highlighted at once. With `defaultColor: false` shiki writes no colour of its
// own: every token carries `--shiki-light` and `--shiki-dark`, and the CSS in CodeBlock decides
// which one is painted. That is what makes the panel follow the app theme instantly — the
// alternative, re-highlighting on every switch, would rebuild every block on the page.
const THEMES = { light: 'github-light-default', dark: 'github-dark-default' } as const
const PLAIN_TEXT = 'text'

let highlighter: Highlighter | null = null
let creating: Promise<Highlighter> | null = null
const loadingLanguages = new Map<string, Promise<void>>()

async function getHighlighter(): Promise<Highlighter> {
  if (highlighter) return highlighter
  if (!creating) {
    creating = createHighlighter({ themes: Object.values(THEMES), langs: [] }).then((created) => {
      highlighter = created
      return created
    })
  }
  return creating
}

// An unknown language degrades to plain text: shiki has no auto-detection, and an unregistered
// id throws instead of rendering.
function resolveLanguage(lang: string): string {
  const normalized = lang.trim().toLowerCase()
  return normalized in bundledLanguages ? normalized : PLAIN_TEXT
}

async function loadLanguageOnce(instance: Highlighter, language: string): Promise<void> {
  if (language === PLAIN_TEXT || instance.getLoadedLanguages().includes(language)) return
  const pending = loadingLanguages.get(language)
    ?? instance.loadLanguage(language as BundledLanguage).then(() => undefined)
  loadingLanguages.set(language, pending)
  await pending
}

export function useHighlighter() {
  async function highlight(code: string, lang: string): Promise<string> {
    const instance = await getHighlighter()
    const language = resolveLanguage(lang)
    await loadLanguageOnce(instance, language)
    return instance.codeToHtml(code, { lang: language, themes: THEMES, defaultColor: false })
  }

  return { highlight }
}
