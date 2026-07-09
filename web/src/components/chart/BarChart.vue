<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { scaleBand, scaleLinear, type ScaleBand, type ScaleLinear } from 'd3-scale'
import ChartInfo from './ChartInfo.vue'

export type BarMode = 'grouped' | 'stacked'
export type BarOrientation = 'vertical' | 'horizontal'

export interface BarSeries {
  name: string
  color?: string
  /** Values aligned 1:1 with `categories`. Missing/non-finite → treated as 0. */
  data: number[]
  /** Optional comparison values (e.g. previous period) — shown as a second,
   *  greyed column in the tooltip; not drawn as bars. */
  compareData?: number[]
}

interface Props {
  /** Category labels (one bar group per category). */
  categories: string[]
  series: BarSeries[]
  /** `grouped` — bars side by side; `stacked` — bars on top of each other. */
  mode?: BarMode
  /** Bar direction. */
  orientation?: BarOrientation
  /** Total SVG height (px). */
  height?: number
  /** Inner padding for axes & labels. */
  padding?: { top?: number; right?: number; bottom?: number; left?: number }
  /** Value-axis tick count (target). */
  ticks?: number
  /** Force value-axis max (else auto). */
  valueMax?: number
  /** Gap between category bands (0..1). */
  bandPadding?: number
  /** Gap between bars inside a grouped band (0..1). */
  groupPadding?: number
  /** Corner radius for bars (px). */
  radius?: number
  /** Value formatter for axis + tooltip. */
  formatValue?: (v: number) => string
  /** Show value-axis grid lines. */
  grid?: boolean
  /** Show legend strip above chart. */
  legend?: boolean
  /** Per-category flag (1:1 with `categories`) — draws a faint grey backdrop
   *  behind matching bands (e.g. weekends). Vertical orientation only. */
  bandHighlights?: boolean[]
  /** Per-category tooltip header override (1:1 with `categories`); falls back
   *  to the category label. */
  tooltipHeaders?: string[]
  /** Append a total (sum of series) row to the tooltip. */
  showTotal?: boolean
  /** Label for the total row (caller supplies localized text). */
  totalLabel?: string
  /** Per-category sub-header for the comparison column (1:1 with `categories`). */
  compareHeaders?: string[]
  /** Data-source explanation — shown as an info icon (ⓘ) in the top-right corner. */
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'grouped',
  orientation: 'vertical',
  height: 280,
  ticks: 5,
  bandPadding: 0.24,
  groupPadding: 0.12,
  radius: 3,
  grid: true,
  legend: true,
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

const isHorizontal = computed(() => props.orientation === 'horizontal')
const isStacked = computed(() => props.mode === 'stacked')

const inner = computed(() => ({
  w: Math.max(0, width.value - pad.value.left - pad.value.right),
  h: Math.max(0, props.height - pad.value.top - pad.value.bottom),
}))

function colorFor(i: number, s: BarSeries): string {
  return s.color ?? DEFAULT_PALETTE[i % DEFAULT_PALETTE.length]
}

function valueAt(s: BarSeries, ci: number): number {
  const v = s.data[ci]
  return Number.isFinite(v) ? v : 0
}

// Largest value along the value axis — stacked sums per category, else max single value.
const valueMax = computed(() => {
  if (props.valueMax !== undefined) return props.valueMax
  let hi = 0
  props.categories.forEach((_, ci) => {
    if (isStacked.value) {
      const sum = props.series.reduce((acc, s) => acc + Math.max(0, valueAt(s, ci)), 0)
      hi = Math.max(hi, sum)
    } else {
      props.series.forEach((s) => { hi = Math.max(hi, valueAt(s, ci)) })
    }
  })
  return hi || 1
})

// Category (band) scale — runs along the cross axis (x for vertical, y for horizontal).
const bandScale = computed<ScaleBand<string>>(() =>
  scaleBand<string>()
    .domain(props.categories)
    .range(isHorizontal.value ? [0, inner.value.h] : [0, inner.value.w])
    .padding(props.bandPadding),
)

// Inner-band scale for grouped bars (one slot per series).
const groupScale = computed<ScaleBand<string>>(() =>
  scaleBand<string>()
    .domain(props.series.map((s) => s.name))
    .range([0, bandScale.value.bandwidth()])
    .padding(props.groupPadding),
)

// Value scale — runs along the value axis (y for vertical, x for horizontal).
const valueScale = computed<ScaleLinear<number, number>>(() =>
  scaleLinear()
    .domain([0, valueMax.value])
    .nice(props.ticks)
    .range(isHorizontal.value ? [0, inner.value.w] : [inner.value.h, 0]),
)

interface Bar {
  x: number
  y: number
  w: number
  h: number
  color: string
  series: BarSeries
  category: string
  value: number
  ci: number
}

const bars = computed<Bar[]>(() => {
  const out: Bar[] = []
  const barW = isStacked.value ? bandScale.value.bandwidth() : groupScale.value.bandwidth()

  props.categories.forEach((category, ci) => {
    const bandStart = bandScale.value(category) ?? 0
    let stackAcc = 0

    props.series.forEach((s, si) => {
      const value = valueAt(s, ci)
      const color = colorFor(si, s)

      if (isHorizontal.value) {
        const len = valueScale.value(value) - valueScale.value(0)
        const cross = isStacked.value ? bandStart : bandStart + (groupScale.value(s.name) ?? 0)
        const start = isStacked.value ? valueScale.value(stackAcc) : 0
        out.push({ x: start, y: cross, w: Math.max(0, len), h: barW, color, series: s, category, value, ci })
        stackAcc += Math.max(0, value)
      } else {
        const len = valueScale.value(0) - valueScale.value(value)
        const cross = isStacked.value ? bandStart : bandStart + (groupScale.value(s.name) ?? 0)
        const top = isStacked.value ? valueScale.value(stackAcc + Math.max(0, value)) : valueScale.value(value)
        out.push({ x: cross, y: top, w: barW, h: Math.max(0, len), color, series: s, category, value, ci })
        stackAcc += Math.max(0, value)
      }
    })
  })
  return out
})

const defaultFormatValue = (v: number): string => {
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (abs >= 1_000)     return (v / 1_000).toFixed(1).replace(/\.0$/, '') + 'k'
  if (Number.isInteger(v)) return v.toString()
  return v.toFixed(2)
}
const fmtV = computed(() => props.formatValue ?? defaultFormatValue)

const valueTicks = computed(() =>
  valueScale.value.ticks(props.ticks).map((t) => ({
    value: t,
    pos: valueScale.value(t),
  })),
)

const bandTicks = computed(() =>
  props.categories.map((c) => ({
    label: c,
    center: (bandScale.value(c) ?? 0) + bandScale.value.bandwidth() / 2,
  })),
)

// Серый фон под отмеченными полосами (на весь шаг — соседние сливаются в блок).
const highlightRects = computed(() => {
  if (isHorizontal.value || !props.bandHighlights) return []
  const step = bandScale.value.step()
  const gap = step - bandScale.value.bandwidth()
  const out: { x: number; w: number }[] = []
  props.categories.forEach((c, i) => {
    if (!props.bandHighlights![i]) return
    out.push({ x: (bandScale.value(c) ?? 0) - gap / 2, w: step })
  })
  return out
})

// ── Hover / tooltip ───────────────────────────────────────────────────────────
const hovered = ref<{ ci: number; si: number } | null>(null)

function onEnter(b: Bar, si: number) {
  hovered.value = { ci: b.ci, si }
}
function onLeave() { hovered.value = null }

const hasCompare = computed(() => props.series.some((s) => s.compareData))

function compareAt(s: BarSeries, ci: number): number | null {
  const v = s.compareData?.[ci]
  return v === undefined || !Number.isFinite(v) ? null : v
}

const hoverRows = computed(() => {
  if (!hovered.value) return []
  const { ci } = hovered.value
  return props.series.map((s, si) => ({
    color: colorFor(si, s),
    name: s.name,
    value: valueAt(s, ci),
    compare: compareAt(s, ci),
    active: si === hovered.value!.si,
  }))
})

const hoverCompareTotal = computed<number | null>(() => {
  if (!hovered.value || !props.showTotal || !hasCompare.value) return null
  const { ci } = hovered.value
  return props.series.reduce((acc, s) => acc + (compareAt(s, ci) ?? 0), 0)
})

const hoverCompareHeader = computed(() =>
  hovered.value ? props.compareHeaders?.[hovered.value.ci] ?? null : null,
)

const tooltipStyle = computed(() => {
  if (!hovered.value) return { display: 'none' }
  const b = bars.value.find((x) => x.ci === hovered.value!.ci)
  if (!b) return { display: 'none' }
  const anchorX = isHorizontal.value
    ? pad.value.left + Math.max(...bars.value.filter((x) => x.ci === b.ci).map((x) => x.x + x.w))
    : pad.value.left + (bandScale.value(b.category) ?? 0) + bandScale.value.bandwidth() / 2
  const flipRight = anchorX > width.value - 200
  return {
    left: flipRight ? `${anchorX - 12}px` : `${anchorX + 12}px`,
    top: `${pad.value.top + 4}px`,
    transform: flipRight ? 'translateX(-100%)' : 'none',
  }
})

const tooltipHeader = computed(() => {
  if (!hovered.value) return ''
  const ci = hovered.value.ci
  return props.tooltipHeaders?.[ci] ?? props.categories[ci]
})

const hoverTotal = computed<number | null>(() => {
  if (!hovered.value || !props.showTotal) return null
  const { ci } = hovered.value
  return props.series.reduce((acc, s) => acc + valueAt(s, ci), 0)
})

function isDimmed(b: Bar): boolean {
  return hovered.value !== null && hovered.value.ci !== b.ci
}
</script>

<template>
  <div ref="wrapperRef" class="bar-chart" :class="{ 'bar-chart--has-info': props.hint }" :style="{ height: `${props.height}px` }">
    <ChartInfo v-if="props.hint" :text="props.hint" class="bar-chart__info" />
    <div v-if="props.legend && props.series.length" class="bar-chart__legend">
      <span
        v-for="(s, i) in props.series"
        :key="s.name"
        class="bar-chart__legend-item"
      >
        <span class="bar-chart__legend-dot" :style="{ background: colorFor(i, s) }" />
        {{ s.name }}
      </span>
    </div>

    <svg
      class="bar-chart__svg"
      :width="width"
      :height="props.height"
      @mouseleave="onLeave"
    >
      <g :transform="`translate(${pad.left},${pad.top})`">
        <!-- highlighted bands (e.g. weekends) — behind everything -->
        <g v-if="highlightRects.length" class="bar-chart__highlight">
          <rect
            v-for="(r, i) in highlightRects"
            :key="`hl-${i}`"
            :x="r.x" y="0" :width="r.w" :height="inner.h"
          />
        </g>

        <!-- grid (along value axis) -->
        <g v-if="props.grid" class="bar-chart__grid">
          <template v-if="isHorizontal">
            <line
              v-for="t in valueTicks"
              :key="`gx-${t.value}`"
              :x1="t.pos" :x2="t.pos" y1="0" :y2="inner.h"
            />
          </template>
          <template v-else>
            <line
              v-for="t in valueTicks"
              :key="`gy-${t.value}`"
              x1="0" :x2="inner.w" :y1="t.pos" :y2="t.pos"
            />
          </template>
        </g>

        <!-- baseline -->
        <line
          class="bar-chart__baseline"
          :x1="0"
          :x2="isHorizontal ? 0 : inner.w"
          :y1="isHorizontal ? 0 : inner.h"
          :y2="inner.h"
        />

        <!-- bars -->
        <g class="bar-chart__bars">
          <rect
            v-for="(b, i) in bars"
            :key="`b-${i}`"
            :x="b.x"
            :y="b.y"
            :width="b.w"
            :height="b.h"
            :rx="Math.min(props.radius, b.w / 2, b.h / 2)"
            :fill="b.color"
            :class="{ 'bar-chart__bar--dim': isDimmed(b) }"
            @mouseenter="onEnter(b, props.series.indexOf(b.series))"
          />
        </g>

        <!-- value-axis labels -->
        <g class="bar-chart__value-axis">
          <template v-if="isHorizontal">
            <text
              v-for="t in valueTicks"
              :key="`vt-${t.value}`"
              :x="t.pos" :y="inner.h + 8"
              text-anchor="middle"
              dominant-baseline="hanging"
            >
              {{ fmtV(t.value) }}
            </text>
          </template>
          <template v-else>
            <text
              v-for="t in valueTicks"
              :key="`vt-${t.value}`"
              :x="-8" :y="t.pos"
              text-anchor="end"
              dominant-baseline="middle"
            >
              {{ fmtV(t.value) }}
            </text>
          </template>
        </g>

        <!-- category-axis labels -->
        <g class="bar-chart__band-axis">
          <template v-if="isHorizontal">
            <text
              v-for="(t, i) in bandTicks"
              :key="`bt-${i}`"
              :x="-8" :y="t.center"
              text-anchor="end"
              dominant-baseline="middle"
            >
              {{ t.label }}
            </text>
          </template>
          <template v-else>
            <text
              v-for="(t, i) in bandTicks"
              :key="`bt-${i}`"
              :x="t.center" :y="inner.h + 8"
              text-anchor="middle"
              dominant-baseline="hanging"
            >
              {{ t.label }}
            </text>
          </template>
        </g>
      </g>
    </svg>

    <!-- tooltip -->
    <div
      v-if="hoverRows.length"
      class="bar-chart__tooltip"
      :style="tooltipStyle"
    >
      <div class="bar-chart__tt-head">
        {{ tooltipHeader }}
        <span v-if="hoverCompareHeader" class="bar-chart__tt-sub">vs {{ hoverCompareHeader }}</span>
      </div>
      <div
        v-for="(r, i) in hoverRows"
        :key="`tt-${i}`"
        class="bar-chart__tt-row"
        :class="{ 'bar-chart__tt-row--active': r.active, 'bar-chart__tt-row--cmp': hasCompare }"
      >
        <span class="bar-chart__tt-dot" :style="{ background: r.color }" />
        <span class="bar-chart__tt-name">{{ r.name }}</span>
        <strong class="bar-chart__tt-val">{{ fmtV(r.value) }}</strong>
        <span v-if="hasCompare" class="bar-chart__tt-prev">{{ r.compare === null ? '—' : fmtV(r.compare) }}</span>
      </div>
      <div
        v-if="hoverTotal !== null"
        class="bar-chart__tt-row bar-chart__tt-total"
        :class="{ 'bar-chart__tt-row--cmp': hasCompare }"
      >
        <span class="bar-chart__tt-dot" style="opacity: 0" />
        <span class="bar-chart__tt-name">{{ props.totalLabel ?? 'Σ' }}</span>
        <strong class="bar-chart__tt-val">{{ fmtV(hoverTotal) }}</strong>
        <span v-if="hasCompare" class="bar-chart__tt-prev">{{ hoverCompareTotal === null ? '—' : fmtV(hoverCompareTotal) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bar-chart {
  position: relative;
  width: 100%;
  user-select: none;
}

.bar-chart__svg {
  display: block;
  overflow: visible;
}

.bar-chart__info {
  position: absolute;
  top: -2px;
  right: 2px;
  z-index: 2;
}
/* освобождаем место под иконку-пояснение справа */
.bar-chart--has-info .bar-chart__legend {
  right: 24px;
}

.bar-chart__legend {
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

.bar-chart__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.bar-chart__legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.bar-chart__highlight rect {
  fill: var(--text);
  opacity: 0.045;
}

.bar-chart__grid line {
  stroke: var(--border-soft);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.bar-chart__baseline {
  stroke: var(--border);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.bar-chart__bars rect {
  transition: opacity 0.12s;
  cursor: pointer;
}

.bar-chart__bar--dim {
  opacity: 0.35;
}

.bar-chart__value-axis text,
.bar-chart__band-axis text {
  font-family: var(--font-mono);
  font-size: 10px;
  fill: var(--text-faint);
}

.bar-chart__tooltip {
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

.bar-chart__tt-head {
  font-family: var(--font-mono);
  font-size: 11px;
  opacity: 0.7;
  margin-bottom: 6px;
}

.bar-chart__tt-row {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  align-items: center;
  gap: 8px;
  line-height: 1.6;
}

/* со столбцом сравнения — добавляем колонку под прошлое значение */
.bar-chart__tt-row--cmp {
  grid-template-columns: 10px 1fr auto auto;
}

.bar-chart__tt-prev {
  font-family: var(--font-mono);
  font-size: 11px;
  color: #9aa3ad;
  text-align: right;
  min-width: 28px;
}

.bar-chart__tt-sub {
  font-family: var(--font-mono);
  font-size: 10px;
  opacity: 0.6;
  margin-left: 6px;
}

.bar-chart__tt-row--active .bar-chart__tt-name {
  color: #fff;
}

.bar-chart__tt-total {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}
.bar-chart__tt-total .bar-chart__tt-name { color: #fff; }

.bar-chart__tt-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.bar-chart__tt-name {
  color: #C9CFD7;
}

.bar-chart__tt-val {
  font-family: var(--font-mono);
  font-weight: 600;
  color: #fff;
}
</style>
