import { createI18n } from 'vue-i18n'
import { ru as vuetifyRu } from 'vuetify/locale'

import commonRu from '@/locales/ru.json'
// Root-level dictionary (not under features/). design-system is template chrome, not a
// domain module, but keeps its own namespace so t('design-system.*') stays stable.
import designSystemRu from '@/locales/design-system/ru.json'

// Единственная локаль приложения — русская. Механизм i18n сохранён (все строки идут
// через t()), но язык один: переключателя нет, fallback указывает на себя же.
export type AppLocale = 'ru'

type Messages = Record<string, unknown>

// Per-feature dictionaries live at web/src/features/<feature>/locales/ru.json
// They are merged into the global messages tree under a namespace = feature dir name.
const featureModules = import.meta.glob<{ default: Messages }>(
  '@/features/*/locales/ru.json',
  { eager: true },
)

function collectFeatureMessages(): Messages {
  const out: Messages = {}
  for (const path in featureModules) {
    const match = path.match(/\/features\/([^/]+)\/locales\/ru\.json$/)
    if (!match) continue
    out[match[1]] = featureModules[path].default
  }
  return out
}

// `$vuetify` holds Vuetify's own component strings (VDataTable, VPagination, …);
// the locale adapter in plugins/vuetify.ts reads them from this same tree.
const messages = {
  ru: {
    $vuetify: vuetifyRu,
    common: commonRu,
    'design-system': designSystemRu,
    ...collectFeatureMessages(),
  },
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true, // expose `$t`/`$te` in templates (needed where a v-for var shadows `t`)
  locale: 'ru',
  fallbackLocale: 'ru',
  missingWarn: false,
  fallbackWarn: false,
  messages,
})

// Сохранён для совместимости: settings-store держит façade `locale.language` над i18n.
// Язык один, так что вызов лишь подтверждает `ru` и фиксирует <html lang>.
export function setLocale(_locale: AppLocale = 'ru'): void {
  i18n.global.locale.value = 'ru'
  if (typeof document !== 'undefined') document.documentElement.lang = 'ru'
}

if (typeof document !== 'undefined') document.documentElement.lang = 'ru'

export default i18n
