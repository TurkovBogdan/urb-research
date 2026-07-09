import { useI18n } from 'vue-i18n'
import type { FieldDescriptor, ChoiceOption } from './api'

// Field label/description and choice-option labels live on the backend (the `Field`
// metadata in `core._settings`). Same policy as task name/description (see
// AGENTS/docs/i18n.md): the backend does NOT send a key — the frontend derives it from
// the stable `(module, field key)` identity and falls back to the backend literal.
//
// Lookup order:
//   1. `<module>.setting.<key>.<field>` — the module's own feature dictionary
//   2. `settings.catalog.<module>.<key>.<field>` — catch-all for modules without a
//      frontend feature namespace (none currently)
//   3. the backend literal — keeps untranslated fields rendering instead of a raw key
export function useSettingText() {
  const { t, te } = useI18n()

  function pick(module: string, key: string, leaf: string, fallback: string): string {
    const own = `${module}.setting.${key}.${leaf}`
    if (te(own)) return t(own)
    const catalog = `settings.catalog.${module}.${key}.${leaf}`
    if (te(catalog)) return t(catalog)
    return fallback
  }

  // Returns a field descriptor with label/description (and choice-option labels)
  // swapped for their translations. All other props are preserved.
  function localizeField(module: string, field: FieldDescriptor): FieldDescriptor {
    const out: FieldDescriptor = {
      ...field,
      label: pick(module, field.key, 'label', field.label),
      description: pick(module, field.key, 'description', field.description),
    }
    if ('options' in field && Array.isArray(field.options)) {
      ;(out as { options: ChoiceOption[] }).options = field.options.map((o) => ({
        ...o,
        label: pick(module, field.key, `option.${o.code}`, o.label),
      }))
    }
    return out
  }

  return { localizeField }
}
