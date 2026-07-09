import { createHighlighter, type Highlighter } from 'shiki'

const LANGS = [
  'python', 'json', 'javascript', 'typescript', 'bash', 'sql',
  'html', 'css', 'yaml', 'toml', 'markdown', 'vue', 'text',
]

let instance: Highlighter | null = null
let pending: Promise<Highlighter> | null = null

async function getHighlighter(): Promise<Highlighter> {
  if (instance) return instance
  if (pending) return pending
  pending = createHighlighter({ themes: ['github-dark'], langs: LANGS }).then((h) => {
    instance = h
    return h
  })
  return pending
}

export function useHighlighter() {
  async function highlight(code: string, lang: string): Promise<string> {
    const h = await getHighlighter()
    const supported = LANGS.includes(lang) ? lang : 'text'
    return h.codeToHtml(code, { lang: supported, theme: 'github-dark' })
  }

  return { highlight }
}
