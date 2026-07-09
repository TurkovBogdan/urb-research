<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { IconMenu2, IconX } from '@tabler/icons-vue'
import AppSidebar from '@/layout/components/AppSidebar.vue'
import { navigationLoading } from '@/router/progress'
import { useLayoutStore } from '@/layout/store'

const route = useRoute()
const router = useRouter()
const { mobile } = useDisplay()
const layout = useLayoutStore()

const fullscreen = computed(() => route.meta.fullscreen === true)

// Content-zone transition, overridable per-route via `meta.transition`. Bound to the
// destination route's meta, so both the leave and enter use the incoming route's name.
// A name with no matching CSS (e.g. 'none') renders instantly.
const transitionName = computed(() => route.meta.transition ?? 'page')
</script>

<template>
  <VApp>
    <!-- Mobile top bar: hamburger toggles the overlay drawer, brand → home.
         Hidden on desktop (permanent rail) and on fullscreen routes (404). -->
    <VAppBar
      v-if="mobile && !fullscreen"
      class="app-topbar"
      flat
      height="54"
    >
      <!-- Toggles the overlay drawer; the glyph flips to a close (X) while open. -->
      <VBtn
        :icon="layout.mobileOpen ? IconX : IconMenu2"
        variant="text"
        density="comfortable"
        class="app-topbar__menu"
        @click="layout.mobileOpen = !layout.mobileOpen"
      />
      <button type="button" class="app-topbar__brand" @click="router.push('/home')">
        <span class="logo-icon">◈</span>
        <span class="logo-text">Uroboros.Research</span>
      </button>
      <VSpacer />
    </VAppBar>

    <AppSidebar v-if="!fullscreen" />
    <VMain class="main-content">
      <!-- Navigation loading bar — pinned to the top of the content zone, right of
           the sidebar. Driven by the router guards (router/progress.ts); fades in
           only when a hop crosses the show-delay (e.g. a lazy chunk download). -->
      <Transition name="route-progress">
        <VProgressLinear
          v-if="navigationLoading"
          class="route-progress"
          indeterminate
          color="primary"
          height="3"
        />
      </Transition>
      <!-- Transition wraps the content zone only — the sidebar lives outside
           RouterView, so it never animates. `out-in` keeps a single page in the
           layout at a time (no two full-height pages overlapping). `appear` runs
           the enter once on first paint (after the boot splash). Order must be
           Transition > KeepAlive > component. -->
      <RouterView v-slot="{ Component }">
        <Transition :name="transitionName" mode="out-in" appear>
          <KeepAlive>
            <component :is="Component" class="h-100" />
          </KeepAlive>
        </Transition>
      </RouterView>
    </VMain>
  </VApp>
</template>

<style scoped>
/* ── Mobile top bar ─────────────────────────────────────────────────────── */
.app-topbar {
  background: var(--sidebar-bg) !important;  /* inline style from theme */
  border-bottom: 1px solid var(--border-soft) !important;
  box-shadow: none !important;
}
.app-topbar :deep(.v-toolbar__content) {
  padding-inline: 8px;
  gap: 4px;
}
.app-topbar__menu {
  color: var(--text-muted) !important;
}
.app-topbar__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border: 0;
  background: none;
  cursor: pointer;
  border-radius: var(--radius-sm);
  .logo-icon { font-size: 18px; color: var(--accent); line-height: 1; }
  .logo-text { font-size: 14px; font-weight: 600; color: var(--text); letter-spacing: -0.01em; white-space: nowrap; }
}

/* Overlay at the very top of the content zone — does not push the page down. */
.route-progress {
  position: absolute;
  inset: 0 0 auto 0;
  z-index: 6;
}

/* Fade the bar itself in/out so it never pops. */
.route-progress-enter-active,
.route-progress-leave-active {
  transition: opacity 0.2s ease;
}
.route-progress-enter-from,
.route-progress-leave-to {
  opacity: 0;
}
</style>
