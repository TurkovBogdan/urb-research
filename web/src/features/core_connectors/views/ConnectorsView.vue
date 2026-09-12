<script setup lang="ts">
// Единственный экран модуля: карточка на каждую интеграцию — состояние сервиса, баланс,
// проверка, — и настройка подключения в модалке по клику на карточку. Неподключённый сервис
// тоже занимает карточку: «не подключён» должно быть видно там же, где всё остальное, а не
// на отдельной странице.
//
// Карточки всегда разложены по группам справочника: группа отвечает «что это за сервис», и
// её порядок задан бэком. Незнакомая и пустая группа сводятся в «Прочее» — чужой модуль со
// своей группой не обязан быть известен этому экрану.
import { computed, onActivated, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh, IconSettings } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { errorText } from '@/api/errorText'
import { pushToast } from '@/composables/useToasts'
import { ICON_FALLBACK, iconByName } from '@/shared/icons'
import type { TablerIcon } from '@/shared/nav'
import ConnectorBalance from '../components/ConnectorBalance.vue'
import AccessStatusChip from '../components/AccessStatusChip.vue'
import AccessFormDialog from '../components/AccessFormDialog.vue'
import { useGroupLabels } from '../labels'
import {
  checkAccess,
  fetchAccesses,
  fetchConnectorGroups,
  fetchConnectors,
  type AccessView,
  type ConnectorGroup,
  type ConnectorPassport,
} from '../api'

const { t } = useI18n()
const { groupLabel } = useGroupLabels()

const passports = ref<ConnectorPassport[]>([])
const accesses = ref<AccessView[]>([])
const groups = ref<ConnectorGroup[]>([])
const checking = ref<number | null>(null)
const loading = ref(true)
const refreshing = ref(false)
const error = ref<string | null>(null)

interface Card {
  passport: ConnectorPassport
  access: AccessView | null
}

interface Shelf {
  code: string
  title: string
  description: string
  icon: TablerIcon
  cards: Card[]
}

const editing = ref<Card | null>(null)
const formOpen = ref(false)

async function load() {
  refreshing.value = true
  error.value = null
  try {
    const [connectors, rows, reference] = await Promise.all([
      fetchConnectors(),
      fetchAccesses(true),
      fetchConnectorGroups(),
    ])
    passports.value = connectors
    accesses.value = rows
    groups.value = reference
  } catch (e) {
    error.value = errorText(e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

onActivated(load)

const cards = computed<Card[]>(() =>
  passports.value.map(passport => ({
    passport,
    access: accesses.value.find(row => row.connector === passport.service) ?? null,
  })),
)

const UNGROUPED = ''

// Полки строятся от справочника, а не от карточек: порядок групп задаёт бэк, а пустая
// группа не должна оставлять на странице заголовок без содержимого.
const shelves = computed<Shelf[]>(() => {
  const known = new Set(groups.value.map(group => group.code))
  const byGroup = new Map<string, Card[]>()
  for (const card of cards.value) {
    const code = known.has(card.passport.group) ? card.passport.group : UNGROUPED
    byGroup.set(code, [...(byGroup.get(code) ?? []), card])
  }
  const shelves: Shelf[] = groups.value
    .filter(group => byGroup.has(group.code))
    .map(group => ({
      code: group.code,
      title: groupLabel(group, 'name'),
      description: groupLabel(group, 'description'),
      icon: iconByName(group.icon),
      cards: byGroup.get(group.code) as Card[],
    }))
  const ungrouped = byGroup.get(UNGROUPED)
  if (ungrouped) {
    shelves.push({
      code: UNGROUPED,
      title: t('core_connectors.group.other.name'),
      description: t('core_connectors.group.other.description'),
      icon: ICON_FALLBACK,
      cards: ungrouped,
    })
  }
  return shelves
})

// Счётчик считает ПОДКЛЮЧЁННЫЕ, а не «ok»: сорванный балансовый опрос переводит карточку в
// «Ошибка», но доступ при этом заведён и работает — вычитать его из счётчика значит врать.
const connectedCount = computed(
  () =>
    cards.value.filter(
      c => c.access && !['unconfigured', 'disabled'].includes(c.access.status.status),
    ).length,
)

// Заглушка вместо баланса объясняет ПОЧЕМУ его нет: сервис не подключён, выключен,
// не умеет отдавать баланс — три разных повода, и путать их нельзя.
function balancePlaceholder(card: Card): string {
  if (!card.access) return t('core_connectors.balance.unconfigured')
  if (!card.passport.has_balance) return t('core_connectors.balance.unsupported')
  if (card.access.status.status !== 'ok') return card.access.status.detail ?? ''
  return t('core_connectors.balance.unsupported')
}

function edit(card: Card) {
  editing.value = card
  formOpen.value = true
}

// Тело карточки ведёт в ту же модалку, но зовётся по состоянию: подключения ещё нет —
// его заводят, есть — правят.
function cardBodyLabel(card: Card): string {
  const name = card.passport.name
  return card.access === null
    ? t('core_connectors.action.connect_service', { name })
    : t('core_connectors.action.configure_service', { name })
}

// Угловая кнопка одна на все состояния: заведённое подключение проверяют, отсутствующее заводят.
function cardAction(card: Card): { label: string; run: () => void } {
  const name = card.passport.name
  return card.access === null
    ? { label: t('core_connectors.action.connect_service', { name }), run: () => edit(card) }
    : { label: t('core_connectors.action.check_service', { name }), run: () => runCheck(card) }
}

// Итог проверки — новость на несколько секунд, а не состояние карточки: держать под неё
// постоянную полосу значит гнать пустоту в каждой карточке ради строки, которая появляется
// по нажатию и через минуту уже неинтересна.
async function runCheck(card: Card) {
  const access = card.access
  if (access === null) return
  checking.value = access.id
  try {
    const check = await checkAccess(access.id)
    const outcome = check.ok
      ? t('core_connectors.check.ok', { ms: check.latency_ms ?? 0 })
      : (check.error ?? t('core_connectors.check.failed'))
    pushToast(`${card.passport.name}: ${outcome}`, check.ok ? 'success' : 'error')
  } catch (e) {
    pushToast(`${card.passport.name}: ${errorText(e)}`, 'error')
  } finally {
    checking.value = null
  }
}
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('core_connectors.page.title')"
      :description="t('core_connectors.page.description')"
    >
      <template #actions>
        <div v-if="!loading && !error && cards.length" class="kpis">
          <div class="kpi">
            <div class="kpi__value">{{ connectedCount }}/{{ cards.length }}</div>
            <div class="kpi__label">{{ t('core_connectors.kpi.connected') }}</div>
          </div>
        </div>
        <VBtn variant="text" :disabled="refreshing" @click="load">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': refreshing }" /></template>
          {{ t('core_connectors.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <div v-if="loading" class="conn-grid">
      <VCard v-for="c in 3" :key="c" variant="flat" class="conn-card skel-card">
        <VSkeletonLoader type="heading, text, text, text" />
      </VCard>
    </div>

    <VAlert v-else-if="error" type="error" variant="tonal">{{ error }}</VAlert>
    <VAlert v-else-if="cards.length === 0" type="info" variant="tonal">
      {{ t('core_connectors.empty') }}
    </VAlert>

    <template v-else>
      <section v-for="shelf in shelves" :key="shelf.code" class="conn-shelf">
        <header class="shelf-heading">
          <span class="shelf-heading__icon">
            <component :is="shelf.icon" :size="16" :stroke-width="1.7" />
          </span>
          <h2 class="shelf-heading__title">{{ shelf.title }}</h2>
          <p class="shelf-heading__description">{{ shelf.description }}</p>
        </header>
        <VDivider class="mb-3" />

        <div class="conn-grid">
          <VCard
            v-for="card in shelf.cards"
            :key="card.passport.service"
            variant="flat"
            class="conn-card"
            :class="{ 'conn-card--off': card.access?.status.status !== 'ok' }"
          >
            <!-- Действие карточки — иконкой в углу и ВНЕ кликабельного тела: кнопка внутри
                 кнопки ломает клавиатуру и экранный диктор, поэтому она соседний элемент,
                 положенный поверх. У заведённого подключения это проверка, у отсутствующего —
                 настройка: угол один, и карточка не обрастает второй полосой ради одной кнопки. -->
            <VBtn
              icon
              variant="text"
              size="small"
              density="comfortable"
              :ripple="false"
              class="conn-card__probe"
              :loading="checking !== null && checking === card.access?.id"
              :aria-label="cardAction(card).label"
              :title="cardAction(card).label"
              @click="cardAction(card).run()"
            >
              <IconRefresh v-if="card.access" :size="18" />
              <IconSettings v-else :size="18" />
              <!-- Свой загрузчик: штатный у VBtn фиксированного размера 23px и в углу карточки
                   выпирает за иконку, которую подменяет. -->
              <template #loader>
                <VProgressCircular indeterminate :size="18" :width="1.5" />
              </template>
            </VBtn>

            <!-- Кнопка настройки — тело карточки, а не карточка целиком: см. выше. -->
            <div
              class="conn-card__body"
              role="button"
              tabindex="0"
              :aria-label="cardBodyLabel(card)"
              @click="edit(card)"
              @keydown.enter="edit(card)"
              @keydown.space.prevent="edit(card)"
            >
              <header class="conn-card__header">
                <h3 class="conn-card__title">{{ card.passport.name }}</h3>
                <AccessStatusChip :status="card.access?.status ?? null" />
              </header>

              <p class="conn-card__desc">{{ card.passport.description }}</p>

              <div class="conn-card__balance">
                <ConnectorBalance
                  :metrics="card.access?.balance?.metrics ?? []"
                  :error="card.access?.balance?.error ?? null"
                  :placeholder="balancePlaceholder(card)"
                />
              </div>
            </div>
          </VCard>
        </div>
      </section>
    </template>

    <AccessFormDialog
      v-if="editing"
      v-model="formOpen"
      :passport="editing.passport"
      :access="editing.access"
      @saved="load"
      @removed="load"
    />
  </PageLayout>
</template>

<style scoped>
.kpis {
  display: flex;
  align-items: center;
  gap: 28px;
  padding-right: 8px;
}

.kpi { display: flex; flex-direction: column; gap: 3px; }

.kpi__value {
  font-size: 22px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text);
  line-height: 1;
}

.kpi__label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

/* Полки идут подряд одним потоком страницы: разделяет их отступ сверху, а не рамка —
   рамка спорила бы с рамками самих карточек. */
.conn-shelf + .conn-shelf { margin-top: 28px; }

/* Заголовок полки: иконка группы, имя и её пояснение в одну строку. Пояснение прижато к
   имени (а не растянуто вправо), иначе на широком экране оно отрывается от заголовка. */
.shelf-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  margin-bottom: 8px;
}

.shelf-heading__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  flex: none;
  color: var(--accent);
  background: var(--accent-soft);
}

.shelf-heading__title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
  white-space: nowrap;
}

.shelf-heading__description {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-muted);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Одна высота на все карточки, а не на ряд: без `1fr` ряд с двумя метриками баланса выше
   ряда с одной, и сетка идёт лесенкой. Внутри карточки разницу забирает тело (`flex: 1`),
   поэтому плита баланса у всех на одном уровне. */
.conn-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  grid-auto-rows: 1fr;
  gap: 12px;
}

.skel-card { min-height: 180px; padding: var(--card-pad); }
.skel-card :deep(.v-skeleton-loader) { width: 100%; padding: 0; }

/* Отступы держит не карточка, а каждая её часть: нижняя красится отдельным фоном и обязана
   доходить до краёв. Высота плиты задана числом — содержимое баланса разное (метрика с
   долей, метрика без неё, строка «баланса нет»), и без резерва разделитель гулял бы по
   карточкам, хотя сами карточки одной высоты. */
.conn-card {
  --card-pad: 18px;
  --balance-height: 104px;

  position: relative;
  display: flex;
  flex-direction: column;
  padding: 0;
}

/* Иконка проверки лежит поверх карточки в её углу; тело карточки под ней остаётся
   кликабельным, а сама кнопка в него не вложена. Оформление приглушено: карточка про
   баланс, а не про кнопку, поэтому и подложка, и наведение звучат вполголоса. */
.conn-card__probe {
  --v-hover-opacity: 0.03;

  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1;
  color: var(--text-faint);
  transition: color 140ms ease;
}

.conn-card__probe:hover { color: var(--text-muted); }

.conn-card__probe :deep(.v-progress-circular) { opacity: 0.7; }

.conn-card--off { opacity: 0.7; }

/* Кликабельная часть растянута на всю свободную высоту, чтобы полоса действий прижималась
   к низу и карточки в ряду оставались одной высоты. */
.conn-card__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  padding: var(--card-pad) var(--card-pad) 0;
  cursor: pointer;
  transition: background-color 140ms ease;
}

.conn-card__body:hover { background: var(--surface-hover, transparent); }

.conn-card__body:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
}

/* Место под иконку в углу: без отступа статус-чип уезжал бы под неё. */
.conn-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-right: 34px;
}

/* Имя — ровно одна строка: длинное иначе переносится и растит шапку. */
.conn-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Описание — ровно столько строк, сколько указано, а не «до»: короткое резервирует высоту,
   длинное обрезается многоточием. Высота задана жёстко (`height`, не `min-height`) и
   считается от одного числа строк, чтобы обрезка и резерв не разъехались. */
.conn-card__desc {
  --desc-lines: 2;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: -6px 0 0;
  height: calc(1.5em * var(--desc-lines));
  display: -webkit-box;
  -webkit-line-clamp: var(--desc-lines);
  line-clamp: var(--desc-lines);
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Баланс отделён линией во всю ширину карточки: блок выходит из отступов тела отрицательным
   полем и возвращает их себе как внутренние, поэтому линия идёт от края до края, а текст
   остаётся на прежнем месте. */
.conn-card__balance {
  height: var(--balance-height);
  margin: auto calc(-1 * var(--card-pad)) 0;
  padding: 14px var(--card-pad) 0;
  border-top: 1px solid var(--border);
}

</style>
