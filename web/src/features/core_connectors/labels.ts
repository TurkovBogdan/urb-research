import { useI18n } from 'vue-i18n'
import type { ConnectorGroup } from './api'

// Group name/description live on the backend (`core_connectors/connectors/groups.py`), in
// Russian. Same policy as settings fields (see AGENTS/docs/frontend/i18n.md): the backend
// does NOT send a translation key — the frontend derives it from the group code and falls
// back to the backend literal, so a newly added group renders its name instead of a raw key.
//
// Lookup: `core_connectors.group.<code>.<leaf>` → the backend literal.
export function useGroupLabels() {
  const { t, te } = useI18n()

  function groupLabel(group: ConnectorGroup, leaf: 'name' | 'description'): string {
    const key = `core_connectors.group.${group.code}.${leaf}`
    return te(key) ? t(key) : group[leaf]
  }

  return { groupLabel }
}
