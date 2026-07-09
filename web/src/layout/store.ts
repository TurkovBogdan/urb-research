import { defineStore } from 'pinia'
import { ref } from 'vue'

// Ephemeral layout state only — every field resets on reload. The persisted sidebar
// collapse preference lives in stores/settings.ts (ui.sidebarCollapsed).
export const useLayoutStore = defineStore('layout', () => {
  const showTopBar   = ref(true)
  const showBottomBar = ref(true)
  // Mobile-only: the sidebar becomes a temporary overlay; this drives its open
  // state (every page load starts closed).
  const mobileOpen   = ref(false)

  return {
    showTopBar, showBottomBar, mobileOpen,
  }
})
