---
name: box-shadow-subpixel-offset
description: "box-shadow blur on a pseudo-element renders harder/softer depending on the element's sub-pixel offset; fix = compositing layer"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 8307be7c-03e6-47ea-8d15-005e1bfbaca5
---

A blurred `box-shadow` (or gradient/mask edge shadow) on an absolutely-positioned `::before`/`::after` renders at **different crispness depending on the element's sub-pixel position** — e.g. a scroll-edge shadow looks harder when content is shifted by a sidebar and softer when flush at the screen edge (`x=0`). Cause: the blur rasterizes against the **physical pixel grid**, and a fractional offset (sidebar width + fractional `devicePixelRatio`) spreads it across more subpixels. It is NOT in the shadow values.

**Fix:** promote the shadow element to its own compositing layer — `transform: translateZ(0)` (+ `backface-visibility: hidden`). Normalizes the blur regardless of offset. (Confirmed via urb-research; also `will-change: transform` / integer positioning.)

First hit: edge shadows in `web/src/layout/components/EdgeScroller.vue` (the reusable h-scroll wrapper; kanban + tables use it). See task `2026-06-07-design-system-interface-section`.
