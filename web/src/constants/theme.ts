// Colour scheme choice. `system` follows the OS setting and keeps following it while the app
// is open; the other two pin the scheme regardless of what the OS says.
//
// The chosen mode is resolved to a concrete scheme in the settings store, which writes it to
// `<html data-theme>` (the CSS token palettes in styles/main.scss hang off that attribute) and
// hands the same name to Vuetify for its own component colours.

export type ThemeMode = 'system' | 'light' | 'dark'
export type ColorScheme = 'light' | 'dark'

export interface ThemeOption {
  code: ThemeMode
  label: string
  note: string
}

export const THEME_OPTIONS: ThemeOption[] = [
  { code: 'dark', label: 'Тёмная', note: 'Схема приложения по умолчанию.' },
  { code: 'light', label: 'Светлая', note: 'Тот же набор цветов, вывернутый на светлый фон.' },
  { code: 'system', label: 'Системная', note: 'Следует за настройкой операционной системы и переключается вместе с ней.' },
]

export const DEFAULT_THEME: ThemeMode = 'dark'

const DARK_QUERY = '(prefers-color-scheme: dark)'

export function systemScheme(): ColorScheme {
  if (typeof window === 'undefined' || !window.matchMedia) return 'dark'
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light'
}

// Notifies while the OS scheme changes. The caller keeps the subscription for the lifetime of
// the app — the mode can be switched to `system` at any point, so there is nothing to unsubscribe.
export function onSystemSchemeChange(handler: (scheme: ColorScheme) => void): void {
  if (typeof window === 'undefined' || !window.matchMedia) return
  window.matchMedia(DARK_QUERY).addEventListener('change', (event) => {
    handler(event.matches ? 'dark' : 'light')
  })
}

export function resolveScheme(mode: ThemeMode): ColorScheme {
  return mode === 'system' ? systemScheme() : mode
}
