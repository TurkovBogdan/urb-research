export type ScrollMode = 'y' | 'x' | 'both' | 'none'

export function scrollClass(mode: ScrollMode | undefined): string {
  switch (mode ?? 'y') {
    case 'x':    return 'scroll-x'
    case 'both': return 'scroll-both'
    case 'none': return 'scroll-none'
    default:     return 'scroll-y'
  }
}

declare module 'vue-router' {
  interface RouteMeta {
    scroll?:     ScrollMode
    padding?:    boolean    // default: true
    fullscreen?: boolean    // no app chrome (sidebar) — standalone full-bleed screens
    transition?: string     // content-zone <Transition> name; default 'page'. Names with
                            //   no matching CSS (e.g. 'none') render instantly. See App.vue.
  }
}
