<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { extent, max, min, bisector } from 'd3-array'
import { scaleLinear, scaleTime, type ScaleLinear, type ScaleTime } from 'd3-scale'
import { area as d3Area, line as d3Line, curveMonotoneX, curveLinear, curveStepAfter } from 'd3-shape'
import ChartInfo from './ChartInfo.vue'

export type CurveKind = 'smooth' | 'linear' | 'step'
export type XKind = 'time' | 'number'

export interface LinePoint {
  x: number | Date
  y: number
}

export interface LineSeries {
  name: string
  color?: string
  data: LinePoint[]
  /** Override curve per series; defaults to chart-level `curve`. */
  curve?: CurveKind
  /** Render as filled area under line. */
  area?: boolean
  /** Dashed stroke (CSS dasharray). */
  dashed?: boolean
}

interface Props {
  series: LineSeries[]
  /** Auto-detected from first point if omitted. */
  xType?: XKind
  curve?: CurveKind
  /** Total SVG height (px). */
  height?: number
  /** Inner padding for axes & labels. */
  padding?: { top?: number; right?: number; bottom?: number; left?: number }
  /** Y-axis tick count (target). */
  yTicks?: number
  /** X-axis tick count (target). */
  xTicks?: number
  /** Force Y domain min (else auto). */
  yMin?: number
  /** Force Y domain max (else auto). */
  yMax?: number
  /** Format helpers (overrideable via slots too). */
  formatX?: (v: number | Date) => string
  formatY?: (v: number) => string
  /** Show horizontal grid lines. */
  grid?: boolean
  /** Show legend strip above chart. */
  legend?: boolean
  /** Stroke width for lines. */
  strokeWidth?: number
  /** Show dot for each data point on hover series. */
  showPoints?: boolean
  /** Data-source explanation — shown as an info icon (ⓘ) in the top-right corner. */
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  curve: 'smooth',
  height: 280,
  yTicks: 5,
  xTicks: 6,
  grid: true,
  legend: true,
  strokeWidth: 2,
  showPoints: false,
})

const DEFAULT_PALETTE = [
  '#008890', // accent
  '#3A88E4', // legacy info blue
  '#D88000', // warn
  '#7048e8',
  '#2f9e44',
  '#e8590c',
  '#c2255c',
  '#1971c2',
]

const PADDING_DEFAULTS = { top: 12, right: 16, bottom: 28, left: 44 }
const pad = computed(() => ({ ...PADDING_DEFAULTS, ...(props.padding ?? {}) }))

const wrapperRef = ref<HTMLElement | null>(null)
const width = ref(640)

let ro: ResizeObserver | null = null
onMounted(() => {
  if (!wrapperRef.value) return
  ro = new ResizeObserver((entries) => {
    const w = entries[0]?.contentRect.width
    if (w && w > 0) width.value = Math.floor(w)
  })
  ro.observe(wrapperRef.value)
  width.value = wrapperRef.value.clientWidth || 640
})
onBeforeUnmount(() => ro?.disconnect())

const xKind = computed<XKind>(() => {
  if (props.xType) return props.xType
  const firstPoint = props.series.find((s) => s.data.length)?.data[0]
  return firstPoint?.x instanceof Date ? 'time' : 'number'
})

const inner = computed(() => ({
  w: Math.max(0, width.value - pad.value.left - pad.value.right),
  h: Math.max(0, props.height - pad.value.top - pad.value.bottom),
}))

const allPoints = computed(() => props.series.flatMap((s) => s.data))

const xScale = computed<ScaleTime<number, number> | ScaleLinear<number, number>>(() => {
  const xs = allPoints.value.map((p) => (p.x instanceof Date ? p.x.getTime() : (p.x as number)))
  const [lo, hi] = extent(xs) as [number, number] | [undefined, undefined]
  const domain: [number, number] = [lo ?? 0, hi ?? 1]
  if (xKind.value === 'time') {
    return scaleTime().domain([new Date(domain[0]), new Date(domain[1])]).range([0, inner.value.w])
  }
  return scaleLinear().domain(domain).range([0, inner.value.w])
})

const yScale = computed<ScaleLinear<number, number>>(() => {
  const ys = allPoints.value.map((p) => p.y)
  const lo = props.yMin ?? (min(ys) ?? 0)
  const hi = props.yMax ?? (max(ys) ?? 1)
  const span = hi - lo || 1
  const padded: [number, number] = [
    props.yMin !== undefined ? lo : Math.min(lo, lo - span * 0.05),
    props.yMax !== undefined ? hi : hi + span * 0.05,
  ]
  // Snap to zero baseline when all positive & lo is close to 0.
  if (props.yMin === undefined && lo >= 0 && lo / (hi || 1) < 0.2) padded[0] = 0
  return scaleLinear().domain(padded).nice(props.yTicks).range([inner.value.h, 0])
})

function curveOf(kind?: CurveKind) {
  switch (kind ?? props.curve) {
    case 'linear': return curveLinear
    case 'step':   return curveStepAfter
    default:       return curveMonotoneX
  }
}

function xVal(p: LinePoint): number {
  return p.x instanceof Date ? p.x.getTime() : (p.x as number)
}

function colorFor(i: number, s: LineSeries): string {
  return s.color ?? DEFAULT_PALETTE[i % DEFAULT_PALETTE.length]
}

const linePaths = computed(() =>
  props.series.map((s, i) => {
    const gen = d3Line<LinePoint>()
      .x((p) => xScale.value(p.x instanceof Date ? p.x : (p.x as number)) as number)
      .y((p) => yScale.value(p.y))
      .curve(curveOf(s.curve))
      .defined((p) => Number.isFinite(p.y))
    return { d: gen(s.data) ?? '', color: colorFor(i, s), series: s }
  }),
)

const areaPaths = computed(() =>
  props.series.map((s, i) => {
    if (!s.area) return null
    const baseline = yScale.value(Math.max(0, yScale.value.domain()[0]))
    const gen = d3Area<LinePoint>()
      .x((p) => xScale.value(p.x instanceof Date ? p.x : (p.x as number)) as number)
      .y0(baseline)
      .y1((p) => yScale.value(p.y))
      .curve(curveOf(s.curve))
      .defined((p) => Number.isFinite(p.y))
    return { d: gen(s.data) ?? '', color: colorFor(i, s) }
  }),
)

const yTickMarks = computed(() => {
  const ticks = yScale.value.ticks(props.yTicks)
  return ticks.map((t) => ({ value: t, y: yScale.value(t) }))
})

const xTickMarks = computed(() => {
  const raw = (xScale.value as ScaleTime<number, number>).ticks(props.xTicks)
  return raw.map((t: Date | number) => ({
    value: t,
    x: xScale.value(t as never) as number,
  }))
})

const defaultFormatY = (v: number): string => {
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (abs >= 1_000)     return (v / 1_000).toFixed(1).replace(/\.0$/, '') + 'k'
  if (Number.isInteger(v)) return v.toString()
  return v.toFixed(2)
}

const defaultFormatX = (v: number | Date): string => {
  if (v instanceof Date) {
    const m = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    return `${v.getDate()} ${m[v.getMonth()]}`
  }
  return defaultFormatY(v as number)
}

const fmtY = computed(() => props.formatY ?? defaultFormatY)
const fmtX = computed(() => props.formatX ?? defaultFormatX)

// ── Hover / tooltip ─────────────────────────────────────────────────────────
const hoverX = ref<number | null>(null) // mouse-relative inside SVG plot
const xBisect = bisector<LinePoint, number>((p) => xVal(p)).left

interface HoverRow {
  series: LineSeries
  color: string
  point: LinePoint
  cx: number
  cy: number
}

const hoverRows = computed<HoverRow[]>(() => {
  if (hoverX.value === null) return []
  const inverted = (xScale.value.invert as (px: number) => number | Date)(hoverX.value)
  const target = inverted instanceof Date ? inverted.getTime() : (inverted as number)
  const rows: HoverRow[] = []
  props.series.forEach((s, i) => {
    if (!s.data.length) return
    const idx = xBisect(s.data, target, 1)
    const before = s.data[idx - 1]
    const after = s.data[idx]
    const nearest = !after ? before : !before ? after :
      Math.abs(xVal(after) - target) < Math.abs(xVal(before) - target) ? after : before
    if (!nearest || !Number.isFinite(nearest.y)) return
    rows.push({
      series: s,
      color: colorFor(i, s),
      point: nearest,
      cx: xScale.value(nearest.x instanceof Date ? nearest.x : (nearest.x as number)) as number,
      cy: yScale.value(nearest.y),
    })
  })
  return rows
})

const hoverAnchor = computed(() => {
  if (!hoverRows.value.length) return null
  // Snap crosshair to the nearest x across all rows.
  const cx = hoverRows.value.reduce((s, r) => s + r.cx, 0) / hoverRows.value.length
  return cx
})

function onMove(ev: MouseEvent) {
  const svg = (ev.currentTarget as SVGElement).getBoundingClientRect()
  const rel = ev.clientX - svg.left - pad.value.left
  if (rel < 0 || rel > inner.value.w) {
    hoverX.value = null
    return
  }
  hoverX.value = rel
}
function onLeave() { hoverX.value = null }

const tooltipStyle = computed(() => {
  if (hoverAnchor.value === null) return { display: 'none' }
  const xPx = pad.value.left + hoverAnchor.value
  // Flip side when running out of room.
  const flipRight = xPx > width.value - 200
  return {
    left: flipRight ? `${xPx - 12}px` : `${xPx + 12}px`,
    top: `${pad.value.top + 4}px`,
    transform: flipRight ? 'translateX(-100%)' : 'none',
  }
})

const tooltipHeader = computed(() => {
  if (!hoverRows.value.length) return ''
  return fmtX.value(hoverRows.value[0].point.x)
})
</script>

<template>
  <div ref="wrapperRef" class="line-chart" :class="{ 'line-chart--has-info': props.hint }" :style="{ height: `${props.height}px` }">
    <ChartInfo v-if="props.hint" :text="props.hint" class="line-chart__info" />
    <div v-if="props.legend && props.series.length" class="line-chart__legend">
      <span
        v-for="(s, i) in props.series"
        :key="s.name"
        class="line-chart__legend-item"
      >
        <span class="line-chart__legend-dot" :style="{ background: colorFor(i, s) }" />
        {{ s.name }}
      </span>
    </div>

    <svg
      class="line-chart__svg"
      :width="width"
      :height="props.height"
      @mousemove="onMove"
      @mouseleave="onLeave"
    >
      <g :transform="`translate(${pad.left},${pad.top})`">
        <!-- horizontal grid -->
        <g v-if="props.grid" class="line-chart__grid">
          <line
            v-for="t in yTickMarks"
            :key="`gy-${t.value}`"
            x1="0" :x2="inner.w" :y1="t.y" :y2="t.y"
          />
        </g>

        <!-- baseline -->
        <line
          class="line-chart__baseline"
          x1="0" :x2="inner.w"
          :y1="inner.h" :y2="inner.h"
        />

        <!-- areas (below lines) — сплошная заливка в цвет линии -->
        <g class="line-chart__areas">
          <path
            v-for="(a, i) in areaPaths"
            v-show="a"
            :key="`a-${i}`"
            :d="a?.d"
            :fill="a?.color"
            fill-opacity="0.07"
          />
        </g>

        <!-- lines -->
        <g class="line-chart__lines">
          <path
            v-for="(p, i) in linePaths"
            :key="`l-${i}`"
            :d="p.d"
            :stroke="p.color"
            :stroke-width="props.strokeWidth"
            :stroke-dasharray="p.series.dashed ? '4 4' : undefined"
            fill="none"
            stroke-linejoin="round"
            stroke-linecap="round"
          />
        </g>

        <!-- y-axis labels -->
        <g class="line-chart__y-axis">
          <text
            v-for="t in yTickMarks"
            :key="`yt-${t.value}`"
            :x="-8" :y="t.y"
            text-anchor="end"
            dominant-baseline="middle"
          >
            {{ fmtY(t.value) }}
          </text>
        </g>

        <!-- x-axis labels -->
        <g class="line-chart__x-axis" :transform="`translate(0,${inner.h + 8})`">
          <text
            v-for="(t, i) in xTickMarks"
            :key="`xt-${i}`"
            :x="t.x" y="8"
            text-anchor="middle"
            dominant-baseline="hanging"
          >
            {{ fmtX(t.value) }}
          </text>
        </g>

        <!-- crosshair + hover dots -->
        <g v-if="hoverAnchor !== null" class="line-chart__hover">
          <line
            class="line-chart__crosshair"
            :x1="hoverAnchor" :x2="hoverAnchor"
            y1="0" :y2="inner.h"
          />
          <circle
            v-for="(r, i) in hoverRows"
            :key="`hd-${i}`"
            :cx="r.cx" :cy="r.cy"
            r="4"
            :fill="r.color"
            stroke="#fff"
            stroke-width="2"
          />
        </g>

        <!-- always-on data points -->
        <g v-if="props.showPoints" class="line-chart__points">
          <template v-for="(s, i) in props.series" :key="`pts-${i}`">
            <circle
              v-for="(p, j) in s.data"
              :key="`pt-${i}-${j}`"
              :cx="xScale(p.x instanceof Date ? p.x : (p.x as number)) as number"
              :cy="yScale(p.y)"
              r="2.5"
              :fill="colorFor(i, s)"
            />
          </template>
        </g>
      </g>
    </svg>

    <!-- tooltip -->
    <div
      v-if="hoverRows.length"
      class="line-chart__tooltip"
      :style="tooltipStyle"
    >
      <div class="line-chart__tt-head">{{ tooltipHeader }}</div>
      <div
        v-for="(r, i) in hoverRows"
        :key="`tt-${i}`"
        class="line-chart__tt-row"
      >
        <span class="line-chart__tt-dot" :style="{ background: r.color }" />
        <span class="line-chart__tt-name">{{ r.series.name }}</span>
        <strong class="line-chart__tt-val">{{ fmtY(r.point.y) }}</strong>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-chart {
  position: relative;
  width: 100%;
  user-select: none;
}

.line-chart__svg {
  display: block;
  overflow: visible;
}

.line-chart__info {
  position: absolute;
  top: -2px;
  right: 2px;
  z-index: 2;
}
.line-chart--has-info .line-chart__legend {
  right: 24px;
}

.line-chart__legend {
  position: absolute;
  top: -4px;
  right: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-family: var(--font);
  font-size: 11px;
  color: var(--text-muted);
  z-index: 1;
}

.line-chart__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.line-chart__legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.line-chart__grid line {
  stroke: var(--border-soft);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.line-chart__baseline {
  stroke: var(--border);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.line-chart__y-axis text,
.line-chart__x-axis text {
  font-family: var(--font-mono);
  font-size: 10px;
  fill: var(--text-faint);
}

.line-chart__crosshair {
  stroke: var(--text-faint);
  stroke-width: 1;
  stroke-dasharray: 3 3;
  opacity: 0.6;
  pointer-events: none;
}

.line-chart__tooltip {
  position: absolute;
  min-width: 140px;
  padding: 8px 10px;
  background: var(--legacy-tooltip-bg);
  color: #E8ECF0;
  border-radius: var(--radius-sm);
  font-family: var(--font);
  font-size: 12px;
  line-height: 1.4;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
  pointer-events: none;
  z-index: 2;
}

.line-chart__tt-head {
  font-family: var(--font-mono);
  font-size: 11px;
  opacity: 0.7;
  margin-bottom: 6px;
}

.line-chart__tt-row {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  align-items: center;
  gap: 8px;
  line-height: 1.6;
}

.line-chart__tt-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.line-chart__tt-name {
  color: #C9CFD7;
}

.line-chart__tt-val {
  font-family: var(--font-mono);
  font-weight: 600;
  color: #fff;
}
</style>
