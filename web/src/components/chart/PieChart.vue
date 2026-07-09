<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { arc as d3arc, pie as d3pie, type PieArcDatum } from 'd3-shape'
import ChartInfo from './ChartInfo.vue'

export interface PieSlice {
  name: string
  value: number
  color?: string
  /** Optional previous-period value — shown as a greyed «vs» line in the tooltip. */
  compareValue?: number
}

interface Props {
  data: PieSlice[]
  /** Render as a donut (ring); 0 = full pie, 0..1 = inner-radius ratio. */
  donut?: number
  /** Total SVG height (px). The chart is square-ish, sized to height. */
  height?: number
  /** Gap between slices (radians). */
  padAngle?: number
  /** Corner radius for slices (px). */
  cornerRadius?: number
  /** Show legend strip (right of the chart). */
  legend?: boolean
  /** Show percentage labels on slices (hidden for slices below this share). */
  showLabels?: boolean
  /** Hide a slice label when its share is below this fraction (0..1). */
  labelMinShare?: number
  /** Value formatter for tooltip. */
  formatValue?: (v: number) => string
  /** Center caption for donut mode (e.g. total). Defaults to the summed total. */
  centerLabel?: string
  /** Sub-caption under the center label. */
  centerSubLabel?: string
  /** Data-source explanation — shown as an info icon (ⓘ) in the top-right corner. */
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  donut: 0,
  height: 280,
  padAngle: 0.012,
  cornerRadius: 3,
  legend: true,
  showLabels: true,
  labelMinShare: 0.05,
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

function colorFor(i: number, s: PieSlice): string {
  return s.color ?? DEFAULT_PALETTE[i % DEFAULT_PALETTE.length]
}

const total = computed(() =>
  props.data.reduce((acc, s) => acc + Math.max(0, s.value), 0),
)

// Square plot area, left-aligned; the legend occupies the remaining width.
const size = computed(() => Math.max(0, props.height))

// Below this wrapper width the legend can't sit beside the chart without
// clipping (donut + gap eats the row) — stack it underneath as a wrapped row.
const narrow = computed(() => width.value > 0 && width.value < size.value + 160)

// Fixed height while the legend is beside the chart; once stacked the wrapper
// must grow to fit the legend row underneath, so drop to a min-height.
const heightStyle = computed(() =>
  narrow.value ? { minHeight: `${props.height}px` } : { height: `${props.height}px` },
)
const radius = computed(() => size.value / 2 - 6)
const innerRadius = computed(() =>
  props.donut > 0 ? Math.max(0, Math.min(0.95, props.donut)) * radius.value : 0,
)

const arcs = computed<PieArcDatum<PieSlice>[]>(() => {
  const gen = d3pie<PieSlice>()
    .value((s) => Math.max(0, s.value))
    .sort(null)
    .padAngle(props.padAngle)
  return gen(props.data)
})

const arcGen = computed(() =>
  d3arc<PieArcDatum<PieSlice>>()
    .innerRadius(innerRadius.value)
    .outerRadius(radius.value)
    .cornerRadius(props.cornerRadius),
)

// Slightly expanded arc for the hovered slice (pop-out feel without translation).
const arcHover = computed(() =>
  d3arc<PieArcDatum<PieSlice>>()
    .innerRadius(innerRadius.value)
    .outerRadius(radius.value + 6)
    .cornerRadius(props.cornerRadius),
)

interface Segment {
  d: string
  color: string
  slice: PieSlice
  share: number
  labelX: number
  labelY: number
  i: number
}

const segments = computed<Segment[]>(() => {
  const labelArc = d3arc<PieArcDatum<PieSlice>>()
    .innerRadius((radius.value + innerRadius.value) / 2)
    .outerRadius((radius.value + innerRadius.value) / 2)
  return arcs.value.map((a, i) => {
    const [lx, ly] = labelArc.centroid(a)
    return {
      d: arcGen.value(a) ?? '',
      color: colorFor(i, props.data[i]),
      slice: props.data[i],
      share: total.value > 0 ? a.value / total.value : 0,
      labelX: lx,
      labelY: ly,
      i,
    }
  })
})

const defaultFormatValue = (v: number): string => {
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (abs >= 1_000)     return (v / 1_000).toFixed(1).replace(/\.0$/, '') + 'k'
  if (Number.isInteger(v)) return v.toString()
  return v.toFixed(2)
}
const fmtV = computed(() => props.formatValue ?? defaultFormatValue)

const pct = (share: number): string => `${(share * 100).toFixed(share < 0.1 ? 1 : 0)}%`

// ── Hover / tooltip ───────────────────────────────────────────────────────────
const hovered = ref<number | null>(null)
const mouse = ref({ x: 0, y: 0 })

function onEnter(i: number) { hovered.value = i }
function onLeave() { hovered.value = null }
function onMove(ev: MouseEvent) {
  const rect = wrapperRef.value?.getBoundingClientRect()
  if (!rect) return
  mouse.value = { x: ev.clientX - rect.left, y: ev.clientY - rect.top }
}

function pathFor(seg: Segment): string {
  if (hovered.value === seg.i) return arcHover.value(arcs.value[seg.i]) ?? seg.d
  return seg.d
}

const tooltip = computed(() => {
  if (hovered.value === null) return null
  const seg = segments.value[hovered.value]
  if (!seg) return null
  return {
    name: seg.slice.name,
    value: seg.slice.value,
    share: seg.share,
    color: seg.color,
    compare: seg.slice.compareValue ?? null,
  }
})

const tooltipStyle = computed(() => {
  if (!tooltip.value) return { display: 'none' }
  const flipRight = mouse.value.x > width.value - 180
  return {
    left: flipRight ? `${mouse.value.x - 12}px` : `${mouse.value.x + 14}px`,
    top: `${mouse.value.y + 12}px`,
    transform: flipRight ? 'translateX(-100%)' : 'none',
  }
})

const centerPrimary = computed(() =>
  props.centerLabel ?? fmtV.value(total.value),
)
</script>

<template>
  <div
    ref="wrapperRef"
    class="pie-chart"
    :class="{ 'pie-chart--narrow': narrow }"
    :style="heightStyle"
    @mousemove="onMove"
  >
    <ChartInfo v-if="props.hint" :text="props.hint" class="pie-chart__info" />
    <svg
      class="pie-chart__svg"
      :width="size"
      :height="size"
      @mouseleave="onLeave"
    >
      <g :transform="`translate(${size / 2},${size / 2})`">
        <path
          v-for="seg in segments"
          :key="`s-${seg.i}`"
          :d="pathFor(seg)"
          :fill="seg.color"
          class="pie-chart__slice"
          :class="{ 'pie-chart__slice--dim': hovered !== null && hovered !== seg.i }"
          @mouseenter="onEnter(seg.i)"
        />

        <!-- slice percentage labels -->
        <template v-if="props.showLabels">
          <text
            v-for="seg in segments"
            v-show="seg.share >= props.labelMinShare"
            :key="`l-${seg.i}`"
            :x="seg.labelX"
            :y="seg.labelY"
            class="pie-chart__slice-label"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ pct(seg.share) }}
          </text>
        </template>

        <!-- donut center -->
        <template v-if="props.donut > 0">
          <text class="pie-chart__center-primary" text-anchor="middle" dominant-baseline="middle" :y="props.centerSubLabel ? -6 : 0">
            {{ centerPrimary }}
          </text>
          <text
            v-if="props.centerSubLabel"
            class="pie-chart__center-sub"
            text-anchor="middle"
            dominant-baseline="middle"
            :y="13"
          >
            {{ props.centerSubLabel }}
          </text>
        </template>
      </g>
    </svg>

    <!-- legend -->
    <div v-if="props.legend" class="pie-chart__legend">
      <button
        v-for="seg in segments"
        :key="`lg-${seg.i}`"
        class="pie-chart__legend-item"
        :class="{ 'pie-chart__legend-item--dim': hovered !== null && hovered !== seg.i }"
        type="button"
        @mouseenter="onEnter(seg.i)"
        @mouseleave="onLeave"
      >
        <span class="pie-chart__legend-dot" :style="{ background: seg.color }" />
        <span class="pie-chart__legend-name">{{ seg.slice.name }}</span>
        <span class="pie-chart__legend-val">{{ pct(seg.share) }}</span>
      </button>
    </div>

    <!-- tooltip -->
    <div v-if="tooltip" class="pie-chart__tooltip" :style="tooltipStyle">
      <div class="pie-chart__tt-row">
        <span class="pie-chart__tt-dot" :style="{ background: tooltip.color }" />
        <span class="pie-chart__tt-name">{{ tooltip.name }}</span>
      </div>
      <div class="pie-chart__tt-val">
        {{ fmtV(tooltip.value) }} <span class="pie-chart__tt-pct">· {{ pct(tooltip.share) }}</span>
      </div>
      <div v-if="tooltip.compare !== null" class="pie-chart__tt-prev">
        vs {{ fmtV(tooltip.compare) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.pie-chart {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
  user-select: none;
}

/* Narrow container: chart on top, legend as a centered wrapped row underneath
   (otherwise the side legend gets clipped by the card edge). */
.pie-chart--narrow {
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}
.pie-chart--narrow .pie-chart__svg {
  align-self: center;
}
.pie-chart--narrow .pie-chart__legend {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2px 8px;
}
.pie-chart--narrow .pie-chart__legend-item {
  flex: 0 1 auto;
}
.pie-chart--narrow .pie-chart__legend-name {
  flex: 0 1 auto;
}

.pie-chart__info {
  position: absolute;
  top: -2px;
  right: 2px;
  z-index: 2;
}

.pie-chart__svg {
  display: block;
  flex-shrink: 0;
  overflow: visible;
}

.pie-chart__slice {
  transition: opacity 0.12s;
  cursor: pointer;
  stroke: var(--surface);
  stroke-width: 1;
}

.pie-chart__slice--dim {
  opacity: 0.4;
}

.pie-chart__slice-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  fill: #fff;
  pointer-events: none;
}

.pie-chart__center-primary {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 700;
  fill: var(--text);
}

.pie-chart__center-sub {
  font-family: var(--font);
  font-size: 10px;
  fill: var(--text-faint);
}

.pie-chart__legend {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.pie-chart__legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 4px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: var(--font);
  font-size: 12px;
  color: var(--text-muted);
  text-align: left;
  transition: opacity 0.12s, background 0.12s;
}

.pie-chart__legend-item:hover {
  background: var(--surface-hi);
}

.pie-chart__legend-item--dim {
  opacity: 0.4;
}

.pie-chart__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}

.pie-chart__legend-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text);
}

.pie-chart__legend-val {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

.pie-chart__tooltip {
  position: absolute;
  min-width: 120px;
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

.pie-chart__tt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.pie-chart__tt-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.pie-chart__tt-name {
  color: #C9CFD7;
}

.pie-chart__tt-val {
  font-family: var(--font-mono);
  font-weight: 600;
  color: #fff;
}

.pie-chart__tt-pct {
  font-weight: 400;
  opacity: 0.7;
}

.pie-chart__tt-prev {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  font-family: var(--font-mono);
  font-size: 11px;
  color: #9aa3ad;
}
</style>
