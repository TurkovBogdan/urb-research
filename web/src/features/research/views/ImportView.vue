<script setup lang="ts">
// Перенос исследования с другой установки: файл .urch → разбор → план → применение.
//
// Одна страница на четыре состояния, а не четыре адреса: человек ведёт ОДИН архив от выбора до
// отчёта, и разобранный архив всё это время лежит на сервере. Уход с адреса посреди пути бросил бы
// его там, поэтому шаги сменяют друг друга на месте, а отказ от плана явно отзывает загрузку.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  IconAlertTriangle,
  IconCheck,
  IconFileImport,
  IconPackage,
  IconUpload,
} from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import Callout from '@/components/Callout.vue'
import Spoiler from '@/components/Spoiler.vue'
import { errorText } from '@/api/errorText'
import { fmtDateTime } from '@/shared/utils/date'
import { humanSize } from '@/shared/utils/file-icon'

import {
  IMPORT_ENTITIES,
  IMPORT_MODES,
  analyzeImport,
  applyImport,
  cancelImport,
  uploadImportArchive,
  type ImportMode,
  type ImportPlan,
  type ImportReport,
} from '../api'

const { t } = useI18n()

// Что нарисовано на экране — им и названо. «Разбор» и «применение» различаются не запросом в
// полёте, а тем, что человек в этот момент видит и может сделать.
type Screen = 'pick' | 'parse' | 'plan' | 'report'

const screen = ref<Screen>('pick')

// ── Выбор файла ───────────────────────────────────────────────────────────────

const ARCHIVE_EXTENSION = '.urch'

const fileInput = ref<HTMLInputElement | null>(null)
const dropHighlighted = ref(false)
const pickError = ref('')

// `dragleave` прилетает и при переходе курсора на ВЛОЖЕННЫЙ элемент зоны, поэтому подсветку держит
// счётчик входов, а не последнее событие: иначе она гасла бы, стоит курсору наехать на кнопку
// внутри зоны.
let dragDepth = 0

function onDragEnter(): void {
  dragDepth += 1
  dropHighlighted.value = true
}

function onDragLeave(): void {
  dragDepth = Math.max(0, dragDepth - 1)
  dropHighlighted.value = dragDepth > 0
}

function releaseDrag(): void {
  dragDepth = 0
  dropHighlighted.value = false
}

function onDrop(event: DragEvent): void {
  releaseDrag()
  acceptDroppedFiles(event.dataTransfer?.files ?? null)
}

function chooseFile(): void {
  fileInput.value?.click()
}

function onFilePicked(event: Event): void {
  const input = event.target as HTMLInputElement
  acceptDroppedFiles(input.files)
  // Тот же файл, выбранный повторно, не даёт события `change` — пока прежнее значение в поле:
  // человек, поправивший архив и вернувшийся с ним же, иначе нажимал бы в пустоту.
  input.value = ''
}

// Чужое расширение отсекается здесь же, без запроса: сервер ответил бы тем же отказом, только
// после выгрузки целого файла.
function acceptDroppedFiles(files: FileList | null): void {
  if (!files || files.length === 0) return

  if (files.length > 1) {
    pickError.value = t('research.import.pick.one_file')
    return
  }

  const file = files[0]
  if (!file.name.toLowerCase().endsWith(ARCHIVE_EXTENSION)) {
    pickError.value = t('research.import.pick.wrong_extension', { ext: ARCHIVE_EXTENSION })
    return
  }

  pickError.value = ''
  void parseArchive(file)
}

// ── Разбор ────────────────────────────────────────────────────────────────────

// Шагов четыре, а запроса два: выгрузка отвечает за первый, разбор — за остальные три. Отметку
// ставит факт ответа ручки — процентов готовности сервер не присылает и присылать не будет.
const PARSE_STEPS = [
  { code: 'upload', request: 'upload' },
  { code: 'archive', request: 'analyze' },
  { code: 'pages', request: 'analyze' },
  { code: 'registry', request: 'analyze' },
] as const

type ParseRequest = (typeof PARSE_STEPS)[number]['request']

const answeredRequests = ref<ParseRequest[]>([])
const parseError = ref('')

const uploadId = ref('')
const archiveFileName = ref('')
const archiveSize = ref(0)

const plan = ref<ImportPlan | null>(null)

function stepDone(request: ParseRequest): boolean {
  return answeredRequests.value.includes(request)
}

async function parseArchive(file: File): Promise<void> {
  screen.value = 'parse'
  answeredRequests.value = []
  parseError.value = ''
  plan.value = null
  archiveFileName.value = file.name
  archiveSize.value = file.size

  try {
    const upload = await uploadImportArchive(file, { report: false })
    uploadId.value = upload.upload_id
    archiveFileName.value = upload.file_name
    archiveSize.value = upload.size
    answeredRequests.value = ['upload']

    plan.value = await analyzeImport(upload.upload_id, { report: false })
    answeredRequests.value = ['upload', 'analyze']
    screen.value = 'plan'
  } catch (e) {
    parseError.value = errorText(e)
  }
}

// Возврат к выбору файла. Разобранный архив лежит на сервере, и брошенный без отзыва он остался бы
// там мусором; сам отзыв человеку не новость — показывать его отказ незачем.
async function startOver(): Promise<void> {
  const abandoned = uploadId.value

  uploadId.value = ''
  plan.value = null
  report.value = null
  applyError.value = ''
  parseError.value = ''
  pickError.value = ''
  answeredRequests.value = []
  screen.value = 'pick'

  if (abandoned) await cancelImport(abandoned, { report: false }).catch(() => undefined)
}

// ── План ──────────────────────────────────────────────────────────────────────

const PLAN_COLUMNS = ['create', 'update', 'skip', 'merge', 'recode'] as const
const REPORT_COLUMNS = ['created', 'updated', 'skipped', 'merged'] as const

type KnownEntity = (typeof IMPORT_ENTITIES)[number]

function isKnownEntity(entity: string): entity is KnownEntity {
  return (IMPORT_ENTITIES as readonly string[]).includes(entity)
}

// Порядок строк сводки задаёт `IMPORT_ENTITIES`, но незнакомый ключ не выбрасывается, а
// дописывается следом: молча потерянная строка означала бы неполный отчёт о записи в базу.
function summaryEntities(counts: Record<string, unknown>): string[] {
  const keys = Object.keys(counts)
  return [
    ...IMPORT_ENTITIES.filter((entity) => keys.includes(entity)),
    ...keys.filter((entity) => !isKnownEntity(entity)),
  ]
}

function entityLabel(entity: string): string {
  return isKnownEntity(entity) ? t(`research.import.entity.${entity}`) : entity
}

const mode = ref<ImportMode>('newer')

const originLabel = computed(() =>
  plan.value?.archive.same_install
    ? t('research.import.plan.origin_same')
    : t('research.import.plan.origin_other'),
)

// Пустые вёдра предупреждений не показываются вовсе: заголовок с нулём читался бы как найденная
// беда. Порядок — от самого тяжёлого последствия к самому мелкому.
const planWarnings = computed(() => {
  const warnings = plan.value?.warnings
  if (!warnings) return []
  return [
    { code: 'dangling_refs', lines: warnings.dangling_refs },
    {
      code: 'diverged_pages',
      lines: warnings.diverged_pages.map((page) => `${page.url} — ${page.code}`),
    },
    {
      code: 'locally_newer',
      lines: warnings.locally_newer.map(
        (record) => `${entityLabel(record.entity)}: ${record.title} — ${record.code}`,
      ),
    },
    {
      code: 'truncated',
      lines: warnings.truncated.map(
        (record) => `${entityLabel(record.entity)}: ${record.code} — ${record.field}`,
      ),
    },
  ].filter((bucket) => bucket.lines.length > 0)
})

// ── Применение ────────────────────────────────────────────────────────────────

const applying = ref(false)
const report = ref<ImportReport | null>(null)
const applyError = ref('')

const importedResearchPath = computed(() => {
  const root = report.value?.roots[0]
  return root ? `/research/researches/${root.code}` : ''
})

async function apply(): Promise<void> {
  if (!uploadId.value || applying.value) return

  applying.value = true
  applyError.value = ''
  try {
    report.value = await applyImport(uploadId.value, mode.value, { report: false })
    // Применённая загрузка сервером уже снята — отзывать по возврату к выбору файла нечего.
    uploadId.value = ''
  } catch (e) {
    applyError.value = errorText(e)
  } finally {
    applying.value = false
    screen.value = 'report'
  }
}
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.import.page.title')"
      :description="t('research.import.page.description')"
    />

    <!-- ── Зона броска ────────────────────────────────────────────────────────── -->
    <VCard v-if="screen === 'pick'" variant="outlined" rounded="lg">
      <div
        class="drop"
        :class="{ 'drop--highlighted': dropHighlighted }"
        @dragenter.prevent="onDragEnter"
        @dragover.prevent
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
      >
        <IconFileImport :size="44" :stroke-width="1.2" class="drop__icon" />
        <p class="drop__lead">{{ t('research.import.pick.lead') }}</p>
        <p class="drop__hint">{{ t('research.import.pick.hint') }}</p>

        <VBtn color="primary" variant="tonal" :prepend-icon="IconUpload" @click="chooseFile">
          {{ t('research.import.pick.choose') }}
        </VBtn>

        <!-- Отказ стоит в самой зоне: он про то, что сюда бросили, и читается там же, куда
             смотрели. -->
        <VAlert
          v-if="pickError"
          type="error"
          variant="tonal"
          density="compact"
          class="drop__error"
        >
          {{ pickError }}
        </VAlert>

        <input
          ref="fileInput"
          type="file"
          :accept="ARCHIVE_EXTENSION"
          class="drop__input"
          @change="onFilePicked"
        >
      </div>
    </VCard>

    <!-- ── Разбор ─────────────────────────────────────────────────────────────── -->
    <VCard v-else-if="screen === 'parse'" variant="outlined" rounded="lg">
      <VCardText>
        <div class="archive-line">
          <IconPackage :size="18" class="archive-line__icon" />
          <span class="archive-line__name">{{ archiveFileName }}</span>
          <span class="archive-line__size">{{ humanSize(archiveSize) }}</span>
        </div>

        <ul class="steps">
          <li
            v-for="step in PARSE_STEPS"
            :key="step.code"
            class="steps__item"
            :class="{ 'steps__item--done': stepDone(step.request) }"
          >
            <span class="steps__mark">
              <IconCheck v-if="stepDone(step.request)" :size="14" :stroke-width="2.4" />
              <VProgressCircular v-else-if="!parseError" indeterminate size="14" width="2" />
            </span>
            {{ t(`research.import.step.${step.code}`) }}
          </li>
        </ul>

        <template v-if="parseError">
          <VAlert type="error" variant="tonal" density="compact" class="mt-4">
            {{ parseError }}
          </VAlert>
          <VBtn variant="text" class="mt-3" @click="startOver">
            {{ t('research.import.action.restart') }}
          </VBtn>
        </template>
      </VCardText>
    </VCard>

    <!-- ── План ───────────────────────────────────────────────────────────────── -->
    <template v-else-if="screen === 'plan' && plan">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <h2 v-for="root in plan.roots" :key="root.code" class="plan__title">{{ root.title }}</h2>

          <dl class="plan__facts">
            <div class="plan__fact">
              <dt>{{ t('research.import.plan.origin') }}</dt>
              <dd>{{ originLabel }}</dd>
            </div>
            <div class="plan__fact">
              <dt>{{ t('research.import.plan.created_at') }}</dt>
              <dd>{{ fmtDateTime(plan.archive.created_at) }}</dd>
            </div>
            <div class="plan__fact">
              <dt>{{ t('research.import.plan.app_version') }}</dt>
              <dd>{{ plan.archive.app_version }}</dd>
            </div>
            <div class="plan__fact">
              <dt>{{ t('research.import.plan.format_version') }}</dt>
              <dd>{{ plan.archive.format_version }}</dd>
            </div>
            <div class="plan__fact">
              <dt>{{ t('research.import.plan.file') }}</dt>
              <dd>{{ plan.archive.file_name }} · {{ humanSize(plan.archive.size) }}</dd>
            </div>
          </dl>
        </VCardText>
      </VCard>

      <SectionHeader :title="t('research.import.plan.summary')" />
      <VCard variant="outlined" rounded="lg" class="mb-4">
        <VTable density="compact" class="summary">
          <thead>
            <tr>
              <th>{{ t('research.import.col.entity') }}</th>
              <th v-for="column in PLAN_COLUMNS" :key="column" class="summary__count">
                {{ t(`research.import.col.${column}`) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entity in summaryEntities(plan.counts)" :key="entity">
              <td>{{ entityLabel(entity) }}</td>
              <td
                v-for="column in PLAN_COLUMNS"
                :key="column"
                class="summary__count"
                :class="{ 'summary__count--zero': !plan.counts[entity][column] }"
              >
                {{ plan.counts[entity][column] }}
              </td>
            </tr>
          </tbody>
        </VTable>
      </VCard>

      <VCard
        v-if="plan.details.recoded.length || plan.details.updating.length"
        variant="outlined"
        rounded="lg"
        class="mb-4"
      >
        <Spoiler
          v-if="plan.details.recoded.length"
          variant="minimal"
          :title="`${t('research.import.details.recoded')} · ${plan.details.recoded.length}`"
        >
          <ul class="detail-list">
            <li v-for="item in plan.details.recoded" :key="item.from">
              <span class="detail-list__entity">{{ entityLabel(item.entity) }}</span>
              {{ item.title }}
              <span class="detail-list__codes">{{ item.from }} → {{ item.to }}</span>
            </li>
          </ul>
        </Spoiler>

        <Spoiler
          v-if="plan.details.updating.length"
          variant="minimal"
          :title="`${t('research.import.details.updating')} · ${plan.details.updating.length}`"
        >
          <ul class="detail-list">
            <li v-for="item in plan.details.updating" :key="item.code">
              <span class="detail-list__entity">{{ entityLabel(item.entity) }}</span>
              {{ item.title }}
              <span class="detail-list__codes">{{ item.code }}</span>
            </li>
          </ul>
        </Spoiler>
      </VCard>

      <template v-if="planWarnings.length">
        <SectionHeader :title="t('research.import.warning.title')" />
        <VCard variant="outlined" rounded="lg" class="mb-4 warnings">
          <Spoiler
            v-for="bucket in planWarnings"
            :key="bucket.code"
            variant="minimal"
            color="var(--warn)"
          >
            <template #title>
              <IconAlertTriangle :size="15" class="warnings__icon" />
              {{ t(`research.import.warning.${bucket.code}`) }} · {{ bucket.lines.length }}
            </template>
            <ul class="detail-list">
              <li v-for="line in bucket.lines" :key="line">{{ line }}</li>
            </ul>
          </Spoiler>
        </VCard>
      </template>

      <SectionHeader :title="t('research.import.plan.mode')" />
      <VCard variant="outlined" rounded="lg" class="mb-4">
        <VCardText>
          <VBtnToggle v-model="mode" mandatory density="default" variant="tonal" class="mode-toggle">
            <VBtn v-for="value in IMPORT_MODES" :key="value" :value="value">
              {{ t(`research.import.mode.${value}.label`) }}
            </VBtn>
          </VBtnToggle>

          <Callout class="mt-3">{{ t(`research.import.mode.${mode}.hint`) }}</Callout>
        </VCardText>
      </VCard>

      <div class="plan__actions">
        <VBtn color="primary" :loading="applying" @click="apply">
          {{ t('research.import.action.apply') }}
        </VBtn>
        <VBtn variant="text" :disabled="applying" @click="startOver">
          {{ t('research.import.action.cancel') }}
        </VBtn>
      </div>
    </template>

    <!-- ── Отчёт ──────────────────────────────────────────────────────────────── -->
    <template v-else-if="screen === 'report'">
      <!-- Отказ применения читается здесь же, а не тостом: следующий шаг — тот же файл ещё раз,
           и сказать об этом надо там, где человек остановился. -->
      <VCard v-if="applyError" variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <VAlert type="error" variant="tonal" density="compact">
            {{ applyError }}
          </VAlert>
          <Callout tone="warn" class="mt-3" :title="t('research.import.report.failed_title')">
            {{ t('research.import.report.failed_hint') }}
          </Callout>
        </VCardText>
      </VCard>

      <template v-if="report">
        <VCard variant="outlined" rounded="lg" class="mb-3">
          <VCardText>
            <h2 v-for="root in report.roots" :key="root.code" class="plan__title">
              {{ root.title }}
            </h2>

            <dl class="plan__facts">
              <div class="plan__fact">
                <dt>{{ t('research.import.report.refs_rewritten') }}</dt>
                <dd>{{ report.refs_rewritten }}</dd>
              </div>
              <div class="plan__fact">
                <dt>{{ t('research.import.report.dangling') }}</dt>
                <dd>{{ report.dangling_refs.length }}</dd>
              </div>
            </dl>
          </VCardText>
        </VCard>

        <VCard variant="outlined" rounded="lg" class="mb-4">
          <VTable density="compact" class="summary">
            <thead>
              <tr>
                <th>{{ t('research.import.col.entity') }}</th>
                <th v-for="column in REPORT_COLUMNS" :key="column" class="summary__count">
                  {{ t(`research.import.col.${column}`) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="entity in summaryEntities(report.counts)" :key="entity">
                <td>{{ entityLabel(entity) }}</td>
                <td
                  v-for="column in REPORT_COLUMNS"
                  :key="column"
                  class="summary__count"
                  :class="{ 'summary__count--zero': !report.counts[entity][column] }"
                >
                  {{ report.counts[entity][column] }}
                </td>
              </tr>
            </tbody>
          </VTable>
        </VCard>
      </template>

      <div class="plan__actions">
        <VBtn v-if="importedResearchPath" color="primary" :to="importedResearchPath">
          {{ t('research.import.report.open') }}
        </VBtn>
        <VBtn variant="text" @click="startOver">
          {{ t('research.import.report.again') }}
        </VBtn>
      </div>
    </template>
  </PageLayout>
</template>

<style scoped>
/* ── Зона броска ────────────────────────────────────────────────────────────── */

/* Пунктир — приглашение бросить: сплошная рамка карточки вокруг уже есть, и вторая такая же
   читалась бы как вложенный блок, а не как цель. */
.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin: 16px;
  padding: 56px 24px;
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  text-align: center;
  transition: border-color 0.12s ease, background 0.12s ease;
}

.drop--highlighted {
  border-color: rgb(var(--v-theme-primary));
  background: var(--surface-hi);
}

.drop__icon {
  color: var(--text-faint);
}

.drop__lead {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.drop__hint {
  margin: 0;
  max-width: 460px;
  font-size: 13px;
  color: var(--text-muted);
}

.drop__error {
  max-width: 460px;
  text-align: left;
}

.drop__input {
  display: none;
}

/* ── Разбор ─────────────────────────────────────────────────────────────────── */

.archive-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text);
}

.archive-line__icon {
  color: var(--text-faint);
}

.archive-line__name {
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.archive-line__size {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-faint);
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.steps__item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-muted);
}

.steps__item--done {
  color: var(--text);
}

/* Коробка отметки задана явно: галочка и кружок ожидания разного размера, и без неё подписи
   шагов расходятся по левому краю. */
.steps__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex: none;
  color: var(--text-faint);
}

.steps__item--done .steps__mark {
  color: var(--success);
}

/* ── План и отчёт ───────────────────────────────────────────────────────────── */

.plan__title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text);
  text-wrap: balance;
}

.plan__facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px 24px;
  margin: 0;
}

.plan__fact dt {
  font-size: 12px;
  color: var(--text-faint);
}

.plan__fact dd {
  margin: 2px 0 0;
  font-size: 14px;
  color: var(--text);
}

.plan__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Числа держатся моноширинным и правым краем: столбец сводки читается сравнением, а не чтением. */
.summary__count {
  text-align: right;
  font-family: var(--font-mono);
  white-space: nowrap;
}

/* Ноль — это «ничего не произойдёт», и он не должен тянуть взгляд наравне с работой. */
.summary__count--zero {
  color: var(--text-faint);
}

.warnings__icon {
  color: var(--warn);
  vertical-align: text-bottom;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 13px;
  color: var(--text-muted);
}

.detail-list__entity {
  margin-right: 6px;
  color: var(--text-faint);
}

.detail-list__codes {
  margin-left: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-faint);
}
</style>
