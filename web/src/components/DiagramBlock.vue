<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  IconArrowsMinimize,
  IconMaximize,
  IconX,
  IconZoomIn,
  IconZoomOut,
  IconZoomReset,
} from '@tabler/icons-vue'

import { NO_DIAGRAM_HEIGHT, diagramAlign } from '@/constants/diagrams'
import { DEFAULT_DIAGRAM_FONT, DIAGRAM_FONTS, fontFamilyName } from '@/constants/fonts'
import { useSettingsStore } from '@/stores/settings'
import CodeBlock from './CodeBlock.vue'

// Схема из тела документа: mermaid-исходник → SVG. В теле она стоит превью по ширине колонки,
// разглядывают её в полноэкранном режиме — с зумом и панорамой, как на доске. Всё, что не
// отрисовалось (неизвестный тип, синтаксис за пределами парсера), падает обратно в блок кода:
// читатель всё равно видит исходник, а тело не ломается.
const props = defineProps<{ code: string }>()

// Движок рендера — 1.6 МБ (почти весь вес — раскладка ELK), поэтому он приезжает отдельным
// чанком по первой схеме на странице, а не в основном бандле. Промис общий на приложение.
let engine: Promise<typeof import('beautiful-mermaid')> | null = null

function loadEngine() {
  engine ??= import('beautiful-mermaid')
  return engine
}

// Тип диаграммы задаёт первая непустая строка исходника, а не тег фенса (тег всегда `mermaid`).
// Значение — подпись для шапки; отсутствие ключа означает «этот тип рендерер не умеет».
const DIAGRAM_LABEL: Record<string, string> = {
  graph: 'flowchart',
  flowchart: 'flowchart',
  stateDiagram: 'state',
  'stateDiagram-v2': 'state',
  sequenceDiagram: 'sequence',
  classDiagram: 'class',
  erDiagram: 'ER',
  'xychart-beta': 'chart',
}

const label = computed(() => {
  const header = props.code.split('\n').find((line) => line.trim().length)
  return DIAGRAM_LABEL[header?.trim().split(/\s+/)[0] ?? ''] ?? ''
})

// Цвета уезжают в SVG ссылками на токены темы, а не их значениями: библиотека кладёт каждый
// в CSS-переменную на самом <svg> и выводит из них остальную палитру через color-mix(). Смена
// ночной/дневной темы переписывает токены на <html> и доезжает сюда каскадом — без перерисовки
// схемы и без повторной раскладки. Задан весь набор до единого: имена переменных у библиотеки
// совпадают с именами токенов приложения, и незаданная досталась бы схеме из общего каскада —
// то есть случайно, а не по решению.
const THEME_COLORS = {
  bg: 'var(--surface)',
  fg: 'var(--text)',
  muted: 'var(--text-muted)',
  line: 'var(--text-faint)',
  accent: 'var(--accent)',
  surface: 'var(--surface-hi)',
  border: 'var(--border)',
}

// Рендерер вписывает в <style> схемы @import шрифтов с Google Fonts. Приложение локальное, а
// гарнитуры у него свои (styles/fonts.scss) — запрос наружу и не нужен, и не дойдёт при работе
// без сети.
const FONT_IMPORT = /^\s*@import url\('https:\/\/fonts\.googleapis\.com[^\n]*\n/gm

// Гарнитуры подключены субсетами с `font-display: swap` и качаются только когда понадобились —
// то есть в момент первой схемы. Раскладка к этому моменту уже посчитана, поэтому подмена
// шрифта на лету сдвигает подписи прямо на глазах. Ждём нужные начертания до вставки SVG.
// Строка-образец обязана нести кириллицу и латиницу: субсет качается под конкретный текст.
const FONT_SAMPLE = 'Схема Diagram 123'

async function loadFontFaces(family: string): Promise<void> {
  if (!document.fonts) return
  const faces = [`400 13px "${family}"`, `600 13px "${family}"`, '400 13px "JetBrains Mono"']
  await Promise.all(faces.map((face) => document.fonts.load(face, FONT_SAMPLE))).catch(() => undefined)
}

const settings = useSettingsStore()

const family = computed(() =>
  fontFamilyName(DIAGRAM_FONTS, settings.diagrams.font, DEFAULT_DIAGRAM_FONT),
)

// Оформление блока уезжает в CSS переменными: выравнивание — автополями (ширина у блока по
// содержимому, поэтому центрирование делается именно так), потолок высоты — `none`, когда его сняли.
const frame = computed(() => ({
  '--diagram-side-margin': diagramAlign(settings.diagrams.align) === 'center' ? 'auto' : '0',
  '--diagram-max-height':
    settings.diagrams.maxHeight === NO_DIAGRAM_HEIGHT ? 'none' : `${settings.diagrams.maxHeight}px`,
}))

const svg = ref('')
const unsupported = ref(false)

async function draw() {
  if (!label.value) {
    unsupported.value = true
    return
  }
  try {
    const [{ renderMermaidSVG }] = await Promise.all([loadEngine(), loadFontFaces(family.value)])
    svg.value = renderMermaidSVG(props.code, {
      ...THEME_COLORS,
      font: family.value,
      transparent: true,
      padding: 8,
    }).replace(FONT_IMPORT, '')
  } catch {
    svg.value = ''
    unsupported.value = true
  }
}

onMounted(draw)
// Гарнитура запекается в разметку схемы и участвует в раскладке, поэтому её смена — перерисовка,
// в отличие от смены темы, которая доезжает каскадом.
watch([() => props.code, family], draw)

// ── Полноэкранный режим: зум к курсору, панорама перетаскиванием ──────────────
const ZOOM_LIMITS = { min: 0.2, max: 8 }
const ZOOM_STEP = 1.15
// Доля кадра, которую занимает вписанная схема: воздух по краям нужен, чтобы крайние блоки не
// упирались в панель управления и в границу экрана.
const FIT_MARGIN = 0.92

const fullscreen = ref(false)
const stage = ref<HTMLElement | null>(null)
const view = reactive({ scale: 1, x: 0, y: 0 })
const panning = ref(false)
const spaceHeld = ref(false)

const zoomPercent = computed(() => Math.round(view.scale * 100))

const transform = computed(() => `translate(${view.x}px, ${view.y}px) scale(${view.scale})`)

function diagramSize(): { width: number; height: number } | null {
  const rendered = stage.value?.querySelector('svg')
  if (!rendered) return null
  return { width: Number(rendered.getAttribute('width')), height: Number(rendered.getAttribute('height')) }
}

function fit() {
  const size = diagramSize()
  const frame = stage.value
  if (!size || !frame || !size.width || !size.height) return
  const scale = clamp(Math.min(frame.clientWidth / size.width, frame.clientHeight / size.height) * FIT_MARGIN)
  applyScale(scale, (frame.clientWidth - size.width * scale) / 2, (frame.clientHeight - size.height * scale) / 2)
}

function actualSize() {
  const size = diagramSize()
  const frame = stage.value
  if (!size || !frame) return
  applyScale(1, (frame.clientWidth - size.width) / 2, (frame.clientHeight - size.height) / 2)
}

function applyScale(scale: number, x: number, y: number) {
  view.scale = scale
  view.x = x
  view.y = y
}

function clamp(scale: number): number {
  return Math.min(ZOOM_LIMITS.max, Math.max(ZOOM_LIMITS.min, scale))
}

// Зум держит точку под курсором на месте — иначе на пятикратном увеличении интересный узел
// уезжает за кадр с первым же щелчком колеса.
function zoomAt(clientX: number, clientY: number, factor: number) {
  const frame = stage.value?.getBoundingClientRect()
  if (!frame) return
  const pointerX = clientX - frame.left
  const pointerY = clientY - frame.top
  const scale = clamp(view.scale * factor)
  const ratio = scale / view.scale
  applyScale(scale, pointerX - ratio * (pointerX - view.x), pointerY - ratio * (pointerY - view.y))
}

function zoomCenter(factor: number) {
  const frame = stage.value
  if (!frame) return
  const box = frame.getBoundingClientRect()
  zoomAt(box.left + frame.clientWidth / 2, box.top + frame.clientHeight / 2, factor)
}

function onWheel(event: WheelEvent) {
  zoomAt(event.clientX, event.clientY, event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP)
}

// Перетаскивание панорамирует только с зажатым пробелом — иначе из схемы нельзя выделить текст,
// а он в ней настоящий: это SVG, а не картинка. При панорамировании выделение подавляется: без
// `preventDefault` браузер на том же нажатии начинает тянуть выделение, и схема едет вместе с
// подсвеченным текстом.
function onPointerDown(event: PointerEvent) {
  if (!spaceHeld.value) return
  event.preventDefault()
  document.getSelection()?.removeAllRanges()
  panning.value = true
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent) {
  if (!panning.value) return
  view.x += event.movementX
  view.y += event.movementY
}

function onPointerUp(event: PointerEvent) {
  if (!panning.value) return
  panning.value = false
  ;(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId)
}

function onKeyDown(event: KeyboardEvent) {
  if (!fullscreen.value) return
  if (event.code === 'Space') {
    spaceHeld.value = true
    event.preventDefault()
    return
  }
  const shortcut: Record<string, () => void> = {
    '0': fit,
    '1': actualSize,
    '+': () => zoomCenter(ZOOM_STEP),
    '=': () => zoomCenter(ZOOM_STEP),
    '-': () => zoomCenter(1 / ZOOM_STEP),
  }
  shortcut[event.key]?.()
}

function onKeyUp(event: KeyboardEvent) {
  if (event.code !== 'Space') return
  spaceHeld.value = false
  panning.value = false
}

async function open() {
  if (!svg.value) return
  fullscreen.value = true
  await nextTick()
  fit()
}

watch(fullscreen, (isOpen) => {
  if (isOpen) return
  spaceHeld.value = false
  panning.value = false
})

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
})
</script>

<template>
  <CodeBlock v-if="unsupported" :code="code" lang="mermaid" variant="icon" />

  <div v-else-if="!svg" class="diagram-loading">
    <VProgressCircular indeterminate size="16" width="2" />
    загрузка схемы
  </div>

  <figure v-else class="diagram" :style="frame" @dblclick="open">
    <div class="diagram__preview" v-html="svg" />
    <figcaption class="diagram__hint">
      <IconMaximize :size="13" stroke-width="2" />
      двойной клик — во весь экран
    </figcaption>
  </figure>

  <VDialog v-model="fullscreen" fullscreen :scrim="false" transition="fade-transition">
    <div class="viewer">
      <div
        ref="stage"
        class="viewer__stage"
        :class="{ 'viewer__stage--grab': spaceHeld, 'viewer__stage--grabbing': panning }"
        @wheel.prevent="onWheel"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
        @dblclick="fit"
      >
        <div class="viewer__canvas" :style="{ transform }" v-html="svg" />
      </div>

      <button class="viewer__btn viewer__close" title="Закрыть (Esc)" @click="fullscreen = false">
        <IconX :size="18" stroke-width="2" />
      </button>

      <div class="viewer__controls">
        <button class="viewer__btn" title="Отдалить (−)" @click="zoomCenter(1 / ZOOM_STEP)">
          <IconZoomOut :size="17" stroke-width="1.8" />
        </button>
        <span class="viewer__percent">{{ zoomPercent }}%</span>
        <button class="viewer__btn" title="Приблизить (+)" @click="zoomCenter(ZOOM_STEP)">
          <IconZoomIn :size="17" stroke-width="1.8" />
        </button>
        <span class="viewer__divider" />
        <button class="viewer__btn" title="Вписать (0)" @click="fit">
          <IconArrowsMinimize :size="17" stroke-width="1.8" />
        </button>
        <button class="viewer__btn" title="Исходный размер (1)" @click="actualSize">
          <IconZoomReset :size="17" stroke-width="1.8" />
        </button>
      </div>

      <p class="viewer__legend">колесо — масштаб · пробел с перетаскиванием — перемещение</p>
    </div>
  </VDialog>
</template>

<style scoped>
/* Место под схему занимается заранее: первый чанк движка весит полтора мегабайта, и без резерва
   документ подпрыгивал бы в момент его приезда. Сам блок пустой — рамка и заливка нарисовали бы
   объект, которого ещё нет; остаётся только строка о том, что происходит. */
.diagram-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 220px;
  margin: 16px 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

/* Крутилка серая, а не акцентная: загрузка схемы — не событие, о котором стоит сообщать цветом.
   Красится штрих, а не цвет текста: у `VProgressCircular` в умолчаниях проекта стоит
   `color: primary`, и утилитарный класс от него перебивает `color` со своим `!important`. */
.diagram-loading :deep(.v-progress-circular__overlay) {
  stroke: var(--text-faint);
}

/* Ширина по содержимому: рамка на наведении обводит схему, а не пустую полосу до правого края.
   Потолок — вся доступная ширина, дальше схема ужимается. */
.diagram {
  width: fit-content;
  max-width: 100%;
  margin: 16px var(--diagram-side-margin, 0);
  padding: 12px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  transition: border-color .15s, background .15s;
}

.diagram:hover {
  border-color: var(--border);
  background: var(--surface);
}

/* Схема выровнена по левому краю, а не по центру: текст вокруг ограничен колонкой чтения, и
   узкая схема, поставленная по центру полной ширины, отрывается от этой колонки — документ
   перестаёт читаться сверху вниз одной вертикалью. */
.diagram__preview {
  display: flex;
  justify-content: flex-start;
}

/* Превью всегда вписано: разглядывают схему не здесь, а в полноэкранном режиме, поэтому
   горизонтальной прокрутки в теле документа нет. Потолок высоты — настройка: длинная схема иначе
   выдавливает текст, ради которого её и открыли. */
.diagram__preview :deep(svg) {
  max-width: 100%;
  max-height: var(--diagram-max-height, 420px);
  width: auto;
  height: auto;
}

/* Подпись говорит не что это, а что с этим делать: тип схемы читатель видит по самой схеме,
   а вот про полный экран догадаться неоткуда. */
.diagram__hint {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

.viewer {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: var(--bg);
}

.viewer__stage {
  width: 100%;
  height: 100%;
  overflow: hidden;
  touch-action: none;
  cursor: default;
}

/* Пока пробел зажат, холст — инструмент перемещения, а не текст: выделение выключено целиком,
   иначе даже подавленное на нажатии оно оживает от привычного двойного клика или Ctrl+A. */
.viewer__stage--grab {
  cursor: grab;
  user-select: none;
}

.viewer__stage--grabbing { cursor: grabbing; }

/* Начало координат в левом верхнем углу: расчёт зума к курсору исходит из того, что масштаб
   растёт от этой точки, а не от центра кадра.

   `will-change: transform` здесь был вреден: слой уезжает на композитор, растрируется один раз
   в исходном масштабе и дальше растягивается картинкой — векторная схема становилась мыльной.
   Без него браузер перерисовывает SVG на каждом шаге зума, и линии остаются резкими. */
.viewer__canvas {
  transform-origin: 0 0;
}

/* Сброс обязателен: панель уезжает в оверлей за пределы приложения, где браузер рисует на
   `<button>` серую плашку с рамкой — общего сброса у проекта нет. */
.viewer__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  min-width: 32px;
  appearance: none;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: #5b6472;
  cursor: pointer;
  transition: color .12s, background .12s;
}

.viewer__btn:hover {
  color: #16191f;
  background: rgb(0 0 0 / 6%);
}

.viewer__percent {
  min-width: 48px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 12px;
  color: #5b6472;
  user-select: none;
}

.viewer__divider {
  width: 1px;
  height: 20px;
  margin: 0 4px;
  background: rgb(0 0 0 / 12%);
}

/* Управление всегда светлое, в обеих темах: холст под ним — то тёмный, то белый, и панель,
   красящаяся вместе с темой, на половине схем тонула бы. Отсюда же собственные цвета вместо
   токенов — это не элемент интерфейса приложения, а инструмент поверх изображения. Правила
   стоят после кнопочных: плашку рисуют они, а не сброс внутри. */
.viewer__close,
.viewer__controls {
  position: absolute;
  border: 1px solid rgb(0 0 0 / 12%);
  border-radius: var(--radius);
  background: #fff;
}

.viewer__close {
  top: 16px;
  right: 16px;
  width: 34px;
  height: 34px;
}

/* Панель зума стоит по центру нижнего края — с ней работают глазами по центру кадра, а правый
   верхний угол занят закрытием. */
.viewer__controls {
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
}

.viewer__legend {
  position: absolute;
  left: 16px;
  bottom: 24px;
  margin: 0;
  font-size: 11px;
  color: var(--text-faint);
  user-select: none;
}
</style>
