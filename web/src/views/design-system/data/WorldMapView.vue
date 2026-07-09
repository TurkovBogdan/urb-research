<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import WorldMap, { type WorldMapDatum, type ProjectionKind, type ScaleKind } from '@/components/world-map/WorldMap.vue'
import { CONTINENT_LABELS, ALL_CONTINENTS } from '@/components/world-map/continents'

// Synthetic dataset by alpha-2 (matches what intercom_contacts would produce).
const CONTACT_STATS: WorldMapDatum[] = [
  { code: 'RU', value: 4820 },
  { code: 'US', value: 3110 },
  { code: 'DE', value: 1240 },
  { code: 'FR', value: 980 },
  { code: 'GB', value: 1530 },
  { code: 'BR', value: 620 },
  { code: 'IN', value: 2100 },
  { code: 'CN', value: 1850 },
  { code: 'JP', value: 410 },
  { code: 'KR', value: 280 },
  { code: 'CA', value: 540 },
  { code: 'AU', value: 320 },
  { code: 'IT', value: 460 },
  { code: 'ES', value: 380 },
  { code: 'PL', value: 220 },
  { code: 'UA', value: 760 },
  { code: 'TR', value: 290 },
  { code: 'MX', value: 340 },
  { code: 'AR', value: 180 },
  { code: 'ZA', value: 110 },
  { code: 'EG', value: 90 },
  { code: 'NG', value: 70 },
  { code: 'KZ', value: 510 },
  { code: 'BY', value: 280 },
  { code: 'NL', value: 410 },
  { code: 'SE', value: 220 },
  { code: 'NO', value: 140 },
  { code: 'FI', value: 130 },
  { code: 'CH', value: 230 },
]

// Smaller sparse dataset to demo the badge feature.
const LANG_STATS: WorldMapDatum[] = [
  { code: 'RU', value: 6230, label: 'ru' },
  { code: 'US', value: 4810, label: 'en' },
  { code: 'GB', value: 980, label: 'en' },
  { code: 'DE', value: 1140, label: 'de' },
  { code: 'FR', value: 920, label: 'fr' },
  { code: 'ES', value: 540, label: 'es' },
  { code: 'CN', value: 1820, label: 'zh' },
  { code: 'JP', value: 410, label: 'ja' },
  { code: 'BR', value: 730, label: 'pt' },
]

const projection = ref<ProjectionKind>('naturalEarth1')
const scale = ref<ScaleKind>('sqrt')
const showBadges = ref(false)
const badgeMinValue = ref(500)
const colorMin = ref('#e8f1fb')
const colorMax = ref('#1e6fd9')
const visibleContinents = ref<string[]>([...ALL_CONTINENTS])

const continentEntries = Object.entries(CONTINENT_LABELS) as [string, string][]

function toggleContinent(code: string) {
  const idx = visibleContinents.value.indexOf(code)
  if (idx >= 0) {
    if (visibleContinents.value.length > 1) {
      visibleContinents.value = visibleContinents.value.filter((c) => c !== code)
    }
  } else {
    visibleContinents.value = [...visibleContinents.value, code]
  }
}
function allContinentsOn() { visibleContinents.value = [...ALL_CONTINENTS] }

const lastClick = ref<string>('')

function onClick(p: { entry: { alpha2: string; name: string } | null; numeric: string; value: number | null }) {
  lastClick.value = p.entry
    ? `${p.entry.name} (${p.entry.alpha2}) → ${p.value ?? 'no data'}`
    : `numeric=${p.numeric} → ${p.value ?? 'no data'}`
}

const palettePresets: { label: string; min: string; max: string }[] = [
  { label: 'Blue',   min: '#e8f1fb', max: '#1e6fd9' },
  { label: 'Green',  min: '#e7f6ec', max: '#2f9e44' },
  { label: 'Orange', min: '#fff1e6', max: '#e8590c' },
  { label: 'Purple', min: '#f1ecfa', max: '#7048e8' },
]

const projectionItems: { value: ProjectionKind; title: string }[] = [
  { value: 'naturalEarth1', title: 'Natural Earth' },
  { value: 'equalEarth', title: 'Equal Earth' },
  { value: 'mercator', title: 'Mercator' },
]
const scaleItems: { value: ScaleKind; title: string }[] = [
  { value: 'linear', title: 'Linear' },
  { value: 'sqrt', title: 'Square root (√)' },
  { value: 'log', title: 'Logarithmic' },
]

const total = computed(() => CONTACT_STATS.reduce((s, d) => s + d.value, 0))

const { t } = useI18n()
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.world-map.title')"
        :description="t('design-system.page.world-map.description')"
        back-to="/design-system"
      />

      <!-- Basic -->
      <section class="ds-section">
        <p class="ds-label">basic — fill by value + default tooltip</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <WorldMap :data="CONTACT_STATS" @country-click="onClick" />
          <div v-if="lastClick" class="ds-click">
            <span class="ds-label">click:</span>
            <span class="mono">{{ lastClick }}</span>
          </div>
        </VCard>
      </section>

      <!-- Controls -->
      <section class="ds-section">
        <p class="ds-label">configuration — projection · scale · palette · badges · continents</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <div class="ds-controls">
            <VSelect
              v-model="projection"
              :items="projectionItems"
              item-title="title"
              item-value="value"
              label="Projection"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 200px"
            />
            <VSelect
              v-model="scale"
              :items="scaleItems"
              item-title="title"
              item-value="value"
              label="Scale"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 220px"
            />
            <VBtnToggle
              v-model="colorMax"
              variant="outlined"
              divided
              density="compact"
              mandatory
            >
              <VBtn
                v-for="p in palettePresets"
                :key="p.label"
                :value="p.max"
                size="small"
                @click="colorMin = p.min; colorMax = p.max"
              >
                <span class="palette-dot" :style="{ background: p.max }" />
                {{ p.label }}
              </VBtn>
            </VBtnToggle>
            <VSwitch
              v-model="showBadges"
              label="Badges"
              density="compact"
              hide-details
              color="primary"
            />
            <VTextField
              v-if="showBadges"
              v-model.number="badgeMinValue"
              label="Badge threshold"
              type="number"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 160px"
            />
          </div>

          <!-- Continent filter -->
          <div class="continent-bar mt-3">
            <span class="ds-label mb-0">Continents:</span>
            <button
              v-for="[code, label] in continentEntries"
              :key="code"
              class="continent-chip"
              :class="{ 'continent-chip--active': visibleContinents.includes(code) }"
              @click="toggleContinent(code)"
            >
              {{ label }}
            </button>
            <button class="continent-chip continent-chip--reset" @click="allContinentsOn">
              All
            </button>
          </div>

          <WorldMap
            class="mt-3"
            :data="CONTACT_STATS"
            :projection="projection"
            :scale="scale"
            :color-min="colorMin"
            :color-max="colorMax"
            :show-badges="showBadges"
            :badge-min-value="badgeMinValue"
            :visible-continents="visibleContinents"
          />
          <div class="ds-meta mono">total records: {{ total.toLocaleString('en-US') }}</div>
        </VCard>
      </section>

      <!-- Custom tooltip -->
      <section class="ds-section">
        <p class="ds-label">custom tooltip via slot — languages with badge labels</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <WorldMap
            :data="LANG_STATS"
            :show-badges="true"
            :badge-min-value="0"
            color-min="#e7f6ec"
            color-max="#2f9e44"
          >
            <template #tooltip="{ entry, value, topoName }">
              <div class="custom-tt">
                <div class="custom-tt__title">
                  <span class="custom-tt__flag">{{ entry?.alpha2 ?? '??' }}</span>
                  <span>{{ entry?.name ?? topoName ?? '—' }}</span>
                </div>
                <template v-if="value !== null">
                  <div class="custom-tt__row">
                    <span>Contacts</span>
                    <strong>{{ value.toLocaleString('en-US') }}</strong>
                  </div>
                  <div class="custom-tt__row custom-tt__row--muted">
                    <span>Share</span>
                    <span>{{ ((value / total) * 100).toFixed(1) }} %</span>
                  </div>
                </template>
                <div v-else class="custom-tt__row custom-tt__row--muted">
                  No data
                </div>
              </div>
            </template>
          </WorldMap>
        </VCard>
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 1100px; }
.ds-section { margin-bottom: 32px; }
.ds-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 8px;
}
.ds-meta {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-faint);
}
.ds-click {
  margin-top: 10px;
  padding: 6px 10px;
  background: var(--input-bg);
  border-radius: var(--radius-sm, 6px);
  display: flex;
  gap: 8px;
  align-items: center;
}
.ds-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.palette-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: -1px;
  border: 1px solid var(--border);
}
.mono {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}
.continent-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.continent-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  font-size: 12px;
  border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text-faint);
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  user-select: none;
}
.continent-chip--active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.continent-chip--reset {
  font-family: var(--font-mono);
  font-size: 11px;
  opacity: 0.6;
}
.continent-chip--reset:hover { opacity: 1; }

.custom-tt { min-width: 180px; }
.custom-tt__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 6px;
}
.custom-tt__flag {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  background: var(--input-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
}
.custom-tt__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  line-height: 1.5;
}
.custom-tt__row--muted {
  color: var(--text-faint);
  font-size: 11px;
}
</style>
