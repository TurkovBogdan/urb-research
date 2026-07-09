// ============================================================================
// TODO — TEMPORARY WORKAROUND, NOT A REAL FIX.
//
// This sweeps stuck tooltips after the fact. It does NOT address the real cause:
// hover overlays are not closed when their owning page is deactivated by the
// global <KeepAlive>. That root cause matters far more than this patch and should
// be fixed properly — e.g. close overlays on the component's own deactivation
// lifecycle (onDeactivated), or stop relying on a global <KeepAlive> wrapping every
// route, or use a tooltip setup that ties open-state to the activator's lifecycle.
// Until that is done, this guard is a band-aid: prefer investigating WHY Vuetify's
// overlay leaks past KeepAlive deactivation over extending this hack.
// ============================================================================

// Hover tooltips teleport their content to <body> (VOverlay) and close on the
// activator's `mouseleave`. When a click on the hovered element navigates away, the
// global <KeepAlive> deactivates the leaving page before that `mouseleave` ever fires,
// so the tooltip's `isActive` stays true and its body-level overlay lingers on screen.
// Closing the open tooltips through their activators — while those are still in the
// document — lets Vuetify reset its own state before the page detaches.
export function dismissHoverTooltips(): void {
  document.querySelectorAll<HTMLElement>('.v-overlay--active.v-tooltip').forEach(overlay => {
    const activator = overlay.id
      ? document.querySelector<HTMLElement>(`[aria-describedby="${overlay.id}"]`)
      : null
    if (!activator) return

    activator.dispatchEvent(new PointerEvent('pointerleave'))
    activator.dispatchEvent(new MouseEvent('mouseleave'))
  })
}
