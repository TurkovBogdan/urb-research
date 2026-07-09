<script setup lang="ts">
import { computed, ref, shallowRef, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue'
import { geoPath, geoNaturalEarth1, geoMercator, geoEqualEarth, geoCentroid, type ExtendedFeature } from 'd3-geo'
import { feature } from 'topojson-client'
import type { GeometryCollection, Topology } from 'topojson-specification'
import topology from 'world-atlas/countries-110m.json'
import { ISO_3166_BY_NUMERIC, resolveIso, type Iso3166Entry } from './iso3166'
import { NUMERIC_TO_CONTINENT, ALL_CONTINENTS } from './continents'

export type ProjectionKind = 'naturalEarth1' | 'mercator' | 'equalEarth'
export type ScaleKind = 'linear' | 'sqrt' | 'log'

export interface WorldMapDatum {
  code: string // numeric ISO 3166-1, alpha-2, or alpha-3
  value: number
  label?: string // optional override for the on-map badge text
}

interface Props {
  data: WorldMapDatum[]
  projection?: ProjectionKind
  scale?: ScaleKind
  colorMin?: string
  colorMax?: string
  colorEmpty?: string
  stroke?: string
  showBadges?: boolean
  badgeMinValue?: number
  formatValue?: (value: number) => string
  height?: number | string
  visibleContinents?: string[]
  // Allowlist of country ISO codes (numeric / alpha-2 / alpha-3). When non-empty,
  // only these countries are rendered and the projection is fit to them — the
  // continent filter is then ignored for fitting purposes.
  visibleCountries?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  projection: 'naturalEarth1',
  scale: 'sqrt',
  colorMin: '#e8f1fb',
  colorMax: '#1e6fd9',
  colorEmpty: 'var(--input-bg)',
  stroke: 'var(--border)',
  showBadges: false,
  badgeMinValue: 0,
  formatValue: (v: number) => v.toLocaleString('ru-RU'),
  height: 480,
  visibleContinents: () => ALL_CONTINENTS,
  visibleCountries: () => [],
})

const emit = defineEmits<{
  (e: 'country-click', payload: { entry: Iso3166Entry | null; numeric: string; value: number | null }): void
}>()

type CountryFeature = ExtendedFeature<never, { name?: string }> & { id: string }

// ---- Unique clip-path ID per instance (prevents cross-instance conflicts) ----
const clipId = `world-map-clip-${getCurrentInstance()?.uid ?? Math.random().toString(36).slice(2)}`

// ---- Geographic bounding boxes per continent for projection fitting ----
// These define the "canonical" view for each continent, preventing Russia or
// overseas territories from distorting the viewport when a continent subset is selected.
// Bboxes are intentionally tighter than the geographic extreme of each continent
// because Mercator stretches high latitudes (Y blows up near the poles). For Asia
// and NA we trim the northern bound so Siberian/Arctic emptiness doesn't dominate
// the viewport — populated areas still fit comfortably.
const CONTINENT_BBOX: Record<string, [number, number, number, number]> = {
  AF: [-20, -37, 55, 40],
  AS: [25, -12, 148, 58],
  EU: [-28, 34, 67, 72],
  NA: [-172, 5, -50, 75],
  OC: [108, -48, 180, 24],
  SA: [-84, -58, -32, 15],
}

// ---- TopoJSON → GeoJSON features (built once, Antarctica excluded) ----
const topo = topology as unknown as Topology<{ countries: GeometryCollection }>
const ALL_FEATURES: CountryFeature[] = (
  feature(topo, topo.objects.countries) as unknown as { features: CountryFeature[] }
).features.filter((f) => f.id !== '010')

// Per-feature spherical centroid (computed once) — used to decide whether a feature
// belongs to a continent's geographic bbox for fitting purposes.
const FEATURE_CENTROIDS: Record<string, [number, number]> = {}
for (const f of ALL_FEATURES) {
  const c = geoCentroid(f as never) as [number, number]
  if (Number.isFinite(c[0]) && Number.isFinite(c[1])) FEATURE_CENTROIDS[f.id] = c
}

// ---- Country allowlist resolved to numeric ISO codes ----
const visibleCountrySet = computed(() => {
  const out = new Set<string>()
  for (const code of props.visibleCountries) {
    const entry = resolveIso(code)
    if (entry) out.add(entry.numeric)
  }
  return out
})

// ---- Filtered by allowlist (if any) and by visible continents ----
const visibleFeatures = computed(() => {
  const countries = visibleCountrySet.value
  if (countries.size > 0) {
    return ALL_FEATURES.filter((f) => countries.has(f.id))
  }
  const set = new Set(props.visibleContinents)
  if (set.size === ALL_CONTINENTS.length) return ALL_FEATURES
  return ALL_FEATURES.filter((f) => {
    const c = NUMERIC_TO_CONTINENT[f.id]
    return c ? set.has(c) : false
  })
})

// ---- Container sizing ----
const svgRef = ref<SVGSVGElement | null>(null)
const width = ref(800)

// `height` prop = maximum allowed height. Actual rendered height is computed below.
const maxHeight = computed(() => {
  if (typeof props.height === 'number') return props.height
  const n = parseInt(String(props.height), 10)
  return Number.isFinite(n) ? n : 480
})

let observer: ResizeObserver | null = null
onMounted(() => {
  if (!svgRef.value) return
  const el = svgRef.value.parentElement
  if (!el) return
  observer = new ResizeObserver((entries) => {
    const w = entries[0]?.contentRect.width
    if (w && w > 0) width.value = Math.floor(w)
  })
  observer.observe(el)
  width.value = el.clientWidth || 800
})
onBeforeUnmount(() => observer?.disconnect())

function makeProj() {
  return props.projection === 'mercator' ? geoMercator()
       : props.projection === 'equalEarth' ? geoEqualEarth()
       : geoNaturalEarth1()
}

// ---- Two-pass fit: constrain by width → measure natural height → clamp → refit ----
// This prevents the map from stretching to fill a fixed height when the geographic
// extent has a very different aspect ratio than the container.
const layout = computed(() => {
  const w = width.value
  const maxH = maxHeight.value
  const MIN_H = 120
  const PADDING = 24
  const features = visibleFeatures.value
  const fc = { type: 'FeatureCollection' as const, features }

  if (features.length === 0) return { height: maxH, path: geoPath(makeProj()) }

  // When showing a continent subset, fit to centroids of features that belong to a
  // selected continent's geographic bbox. Two reasons to use centroid points instead
  // of feature polygons: (1) excludes outliers like Russia (EU-classified, centroid
  // ~100°E lies outside the EU bbox), (2) avoids antimeridian artifacts in geoPath
  // bounds for features like Fiji whose polygons cross 180°.
  let fittingTarget: object = fc
  const countries = visibleCountrySet.value
  const continentSet = props.visibleContinents
  if (countries.size > 0) {
    // Fit to centroids of the explicitly listed countries — same MultiPoint trick
    // to avoid antimeridian artifacts (e.g. Fiji, USA with Aleutians).
    const points: [number, number][] = []
    for (const f of features) {
      const c = FEATURE_CENTROIDS[f.id]
      if (c) points.push(c)
    }
    if (points.length) {
      fittingTarget = {
        type: 'Feature' as const,
        geometry: { type: 'MultiPoint' as const, coordinates: points },
        properties: {},
      }
    }
  } else if (continentSet.length < ALL_CONTINENTS.length) {
    // Fit to bbox corners directly (not centroids). Centroid-based fitting
    // dropped outlying mainland edges (Mexico, NZ) outside the centroid cloud
    // and let them get clipped. Bbox corners are also immune to antimeridian
    // artifacts since they're plain points.
    const boxes = continentSet.map((c) => CONTINENT_BBOX[c]).filter(Boolean)
    if (boxes.length) {
      const points: [number, number][] = []
      for (const [west, south, east, north] of boxes) {
        points.push([west, south], [east, south], [east, north], [west, north])
      }
      fittingTarget = {
        type: 'Feature' as const,
        geometry: { type: 'MultiPoint' as const, coordinates: points },
        properties: {},
      }
    }
  }

  // Pass 1: fit width-only (large dummy height so width is always the constraint)
  const p1 = makeProj()
  p1.fitSize([w, w * 4], fittingTarget as never)
  const [[, y0], [, y1]] = geoPath(p1).bounds(fittingTarget as never)
  const naturalH = Math.ceil(y1 - y0) + PADDING * 2

  // Pass 2: clamp and refit into the exact final box
  const h = Math.min(maxH, Math.max(MIN_H, naturalH))
  const p2 = makeProj()
  p2.fitSize([w, h], fittingTarget as never)

  return { height: h, path: geoPath(p2) }
})

const pathFn = computed(() => layout.value.path)
const renderHeight = computed(() => layout.value.height)

// ---- Data lookup by numeric ISO ----
const dataByNumeric = computed(() => {
  const map = new Map<string, WorldMapDatum>()
  for (const d of props.data) {
    const entry = resolveIso(d.code)
    if (entry) map.set(entry.numeric, d)
  }
  return map
})

const maxValue = computed(() => {
  let m = 0
  for (const d of props.data) if (d.value > m) m = d.value
  return m
})

// ---- Linear RGB interpolation ----
function parseHex(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16)
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff]
}
function toHex(rgb: [number, number, number]): string {
  return '#' + rgb.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('')
}
function interpolate(t: number): string {
  const a = parseHex(props.colorMin)
  const b = parseHex(props.colorMax)
  const tt = Math.max(0, Math.min(1, t))
  return toHex([a[0] + (b[0] - a[0]) * tt, a[1] + (b[1] - a[1]) * tt, a[2] + (b[2] - a[2]) * tt])
}

function normalize(value: number): number {
  const max = maxValue.value
  if (max <= 0) return 0
  if (props.scale === 'sqrt') return Math.sqrt(value) / Math.sqrt(max)
  if (props.scale === 'log') return Math.log1p(value) / Math.log1p(max)
  return value / max
}

function colorFor(numeric: string): string {
  const d = dataByNumeric.value.get(numeric)
  if (!d || d.value <= 0) return props.colorEmpty
  return interpolate(normalize(d.value))
}

// ---- Centroids for badges ----
const centroids = computed(() => {
  const path = pathFn.value
  const rows: { numeric: string; x: number; y: number; value: number; label: string }[] = []
  for (const f of visibleFeatures.value) {
    const d = dataByNumeric.value.get(f.id)
    if (!d) continue
    if (d.value < props.badgeMinValue) continue
    const [x, y] = path.centroid(f)
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue
    rows.push({
      numeric: f.id,
      x,
      y,
      value: d.value,
      label: d.label ?? props.formatValue(d.value),
    })
  }
  return rows
})

// ---- Tooltip ----
interface TooltipState {
  visible: boolean
  x: number
  y: number
  numeric: string
  entry: Iso3166Entry | null
  value: number | null
  topoName: string
}
const tooltip = shallowRef<TooltipState>({
  visible: false,
  x: 0,
  y: 0,
  numeric: '',
  entry: null,
  value: null,
  topoName: '',
})

function onEnter(evt: MouseEvent, f: CountryFeature) {
  const entry = ISO_3166_BY_NUMERIC[f.id] ?? null
  const d = dataByNumeric.value.get(f.id)
  tooltip.value = {
    visible: true,
    x: evt.offsetX,
    y: evt.offsetY,
    numeric: f.id,
    entry,
    value: d ? d.value : null,
    topoName: f.properties?.name ?? '',
  }
}
function onMove(evt: MouseEvent) {
  if (!tooltip.value.visible) return
  tooltip.value = { ...tooltip.value, x: evt.offsetX, y: evt.offsetY }
}
function onLeave() {
  tooltip.value = { ...tooltip.value, visible: false }
}
function onClick(f: CountryFeature) {
  const entry = ISO_3166_BY_NUMERIC[f.id] ?? null
  const d = dataByNumeric.value.get(f.id)
  emit('country-click', { entry, numeric: f.id, value: d ? d.value : null })
}

function pathFor(f: CountryFeature): string {
  return pathFn.value(f) ?? ''
}

// ---- Legend stops ----
const legendStops = computed(() => {
  const max = maxValue.value
  if (max <= 0) return [] as { value: number; color: string; label: string }[]
  const ticks = [0, 0.25, 0.5, 0.75, 1]
  return ticks.map((t) => ({
    value: t * max,
    color: interpolate(t),
    label: props.formatValue(Math.round(t * max)),
  }))
})
</script>

<template>
  <div class="world-map">
    <div class="world-map__viewport" :style="{ height: `${renderHeight}px` }">
      <svg
        ref="svgRef"
        class="world-map__svg"
        :viewBox="`0 0 ${width} ${renderHeight}`"
        :width="width"
        :height="renderHeight"
        @mousemove="onMove"
        @mouseleave="onLeave"
      >
        <defs>
          <clipPath :id="clipId">
            <rect :width="width" :height="renderHeight" />
          </clipPath>
        </defs>
        <g class="world-map__countries" :clip-path="`url(#${clipId})`">
          <path
            v-for="f in visibleFeatures"
            :key="f.id"
            :d="pathFor(f)"
            :fill="colorFor(f.id)"
            :stroke="stroke"
            stroke-width="0.5"
            class="world-map__country"
            :class="{ 'world-map__country--has-data': dataByNumeric.has(f.id) }"
            @mouseenter="onEnter($event, f)"
            @click="onClick(f)"
          />
        </g>

        <g v-if="showBadges" class="world-map__badges" pointer-events="none" :clip-path="`url(#${clipId})`">
          <g
            v-for="b in centroids"
            :key="b.numeric"
            :transform="`translate(${b.x}, ${b.y})`"
            class="world-map__badge"
          >
            <rect
              :x="-((b.label.length * 4) + 6)"
              y="-9"
              :width="(b.label.length * 8) + 12"
              height="18"
              rx="9"
              ry="9"
              class="world-map__badge-bg"
            />
            <text class="world-map__badge-text" text-anchor="middle" dominant-baseline="central">
              {{ b.label }}
            </text>
          </g>
        </g>
      </svg>

      <div
        v-if="tooltip.visible"
        class="world-map__tooltip"
        :style="{ left: `${tooltip.x + 12}px`, top: `${tooltip.y + 12}px` }"
      >
        <slot name="tooltip" :entry="tooltip.entry" :value="tooltip.value" :numeric="tooltip.numeric" :topo-name="tooltip.topoName">
          <div class="world-map__tooltip-title">
            {{ tooltip.entry?.name ?? tooltip.topoName ?? '—' }}
          </div>
          <div class="world-map__tooltip-row">
            <span class="world-map__tooltip-key">Значение</span>
            <span class="world-map__tooltip-val">
              {{ tooltip.value !== null ? formatValue(tooltip.value) : '—' }}
            </span>
          </div>
          <div v-if="tooltip.entry" class="world-map__tooltip-row">
            <span class="world-map__tooltip-key">ISO</span>
            <span class="world-map__tooltip-val mono">{{ tooltip.entry.alpha2 }} · {{ tooltip.entry.alpha3 }}</span>
          </div>
        </slot>
      </div>
    </div>

    <div v-if="legendStops.length" class="world-map__legend">
      <div
        v-for="stop in legendStops"
        :key="stop.value"
        class="world-map__legend-stop"
      >
        <span class="world-map__legend-swatch" :style="{ background: stop.color }" />
        <span class="world-map__legend-label mono">{{ stop.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.world-map {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.world-map__viewport {
  position: relative;
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.world-map__svg {
  display: block;
  width: 100%;
  height: 100%;
}

.world-map__country {
  transition: fill 0.15s ease, stroke 0.15s ease;
  cursor: pointer;
}
.world-map__country:hover {
  stroke: var(--accent);
  stroke-width: 1;
}
.world-map__country:not(.world-map__country--has-data) {
  cursor: default;
}

.world-map__badge-bg {
  fill: rgba(15, 23, 42, 0.82);
  stroke: rgba(255, 255, 255, 0.4);
  stroke-width: 0.5;
}
.world-map__badge-text {
  fill: #fff;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
}

.world-map__tooltip {
  position: absolute;
  pointer-events: none;
  min-width: 160px;
  padding: 8px 10px;
  background: var(--surface-hi, var(--surface));
  border: 1px solid var(--border);
  border-radius: var(--radius-sm, 6px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  font-size: 12px;
  color: var(--text);
  z-index: 5;
}
.world-map__tooltip-title {
  font-weight: 600;
  margin-bottom: 4px;
}
.world-map__tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  line-height: 1.4;
}
.world-map__tooltip-key {
  color: var(--text-faint);
}
.world-map__tooltip-val {
  color: var(--text);
}

.world-map__legend {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 0 4px;
}
.world-map__legend-stop {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.world-map__legend-swatch {
  display: inline-block;
  width: 16px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid var(--border);
}
.world-map__legend-label {
  font-size: 11px;
  color: var(--text-muted);
}
.mono {
  font-family: var(--font-mono);
}
</style>
