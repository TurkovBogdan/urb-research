---
title: Design system — bar chart + pie chart
date: 2026-05-31
status: completed
description: "Add bar (столбцы) and pie/donut (круговая диаграмма) chart components + showcase pages to the design system, mirroring the existing D3-based LineChart pattern."
tags: [frontend, design-system, charts]
---

## Task

User: «Дизайн система, у нас есть линейный график, теперь нужны столбцы и круговая диаграма отдельными страницами и компонентами».

## Context

Design system already has a D3-based `LineChart.vue` component (`web/src/components/chart/`) plus a `LineChartView.vue` showcase under the `charts` group. No charting library — pure SVG + d3-scale/d3-shape/d3-array. Need to extend with bar and pie following the same conventions (palette, CSS tokens, ResizeObserver, hover tooltip, legend, showcase sections, route, index card, locales).

## What was done

- `web/src/components/chart/BarChart.vue` — D3 SVG bar chart (categories + multi-series, grouped/stacked, vertical/horizontal, hover tooltip, legend).
- `web/src/components/chart/PieChart.vue` — D3 SVG pie/donut (slices, hover, legend, percentage labels, donut center total).
- `BarChartView.vue` + `PieChartView.vue` showcase pages.
- Routes in `routes.ts`; index cards in `DesignSystemIndexView.vue` (`charts` group); locale entries (en/ru).

## Result

New, no charting library — pure SVG + d3-scale/d3-shape, mirroring `LineChart.vue`:

- `web/src/components/chart/BarChart.vue` — `categories` + `BarSeries[]`; `mode` grouped|stacked, `orientation` vertical|horizontal; `scaleBand`/`scaleLinear`; grid, value/category axes, per-category hover tooltip (dims other bands), legend, rounded bars.
- `web/src/components/chart/PieChart.vue` — `PieSlice[]`; `donut` ratio (0 = pie), `d3.pie`/`d3.arc`; slice % labels (hidden under `labelMinShare`), donut center total/sub-label, clickable+hoverable legend, pop-out hovered slice, cursor-following tooltip.
- `web/src/features/design-system/views/BarChartView.vue` — 7 sections (single / grouped / stacked / horizontal / horizontal-stacked / compact / playground).
- `web/src/features/design-system/views/PieChartView.vue` — 6 sections (pie / donut+total / two-slice / many / compact-no-labels / playground).
- Routes `/design-system/bar-chart` + `/design-system/pie-chart` (`routes.ts`); index cards under `charts` group with `IconChartBar`/`IconChartPie` (`DesignSystemIndexView.vue`); en/ru locale entries (`index.page.*` + `page.*`).

`vue-tsc --noEmit` clean. Browser verification skipped (user declined).

