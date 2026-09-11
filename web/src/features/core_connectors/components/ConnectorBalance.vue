<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { BalanceMetric } from '../api'

// Вывод баланса — на массиве метрик: у коннектора может быть несколько показателей
// (баланс, лимит ключа, кредиты — одно другое не отменяет), выводим что доступно. Каждая
// строка единообразна: лейбл + значение (+подпись) + прогресс-бар (всегда; пустой для денег/
// ошибки/«нет баланса»). `error` рисует строку-ошибку, `placeholder` — заглушку «нет баланса».
const props = defineProps<{
  metrics: BalanceMetric[]
  error?: string | null
  placeholder?: string
}>()

const { t, locale } = useI18n()

function fmtMoney(amount: number, currency: string): string {
  return new Intl.NumberFormat(locale.value === 'en' ? 'en-US' : 'ru-RU', {
    style: 'currency',
    currency,
  }).format(amount)
}

function fmtNum(n: number): string {
  return n.toLocaleString(locale.value === 'en' ? 'en-US' : 'ru-RU')
}

// Единица печатается рядом с числом, только когда она добавляет смысл. У счётной метрики
// («Кредиты» — 0 / 1 000 кредитов) она повторяет подпись строки, а у денежной называет
// валюту, которой в подписи нет. Признак — форма кода: три заглавные буквы = ISO-валюта.
const CURRENCY_CODE = /^[A-Z]{3}$/

function unitLabel(unit: string | null): string {
  if (!unit || !CURRENCY_CODE.test(unit)) return ''
  return t(`core_connectors.balance.unit.${unit}`, unit)
}

interface Row {
  key: string
  kind: 'metric' | 'error' | 'na'
  label: string | null
  value: string
  note: string | null
  ratio: number | null // доля использования для бара (null → пустой бар)
}

const rows = computed<Row[]>(() => {
  if (props.error) {
    return [{ key: 'error', kind: 'error', label: null, value: props.error, note: null, ratio: null }]
  }
  if (props.metrics.length === 0) {
    return [{ key: 'na', kind: 'na', label: null, value: props.placeholder ?? '', note: null, ratio: null }]
  }
  return props.metrics.map((m, i): Row => {
    const value =
      m.amount != null
        ? fmtMoney(m.amount, m.currency ?? 'USD')
        : m.used != null && m.total != null
          ? `${fmtNum(m.used)} / ${fmtNum(m.total)} ${unitLabel(m.unit)}`.trim()
          : '—'
    return {
      key: `${m.label}-${i}`,
      kind: 'metric',
      label: m.label,
      value,
      note:
        m.used_percent != null
          ? t('core_connectors.balance.used_percent', { percent: fmtNum(m.used_percent) })
          : null,
      ratio: m.used_percent != null ? m.used_percent / 100 : null,
    }
  })
})
</script>

<template>
  <div class="balance">
    <div v-for="row in rows" :key="row.key" class="metric">
      <div class="metric__label">{{ row.label }}</div>
      <div class="metric__value" :class="`is-${row.kind}`" :title="row.value">{{ row.value }}</div>
      <div class="metric-bar">
        <span
          class="metric-bar__fill"
          :class="{ 'is-high': (row.ratio ?? 0) > 0.85 }"
          :style="{ width: `${Math.round((row.ratio ?? 0) * 100)}%` }"
        />
      </div>
      <div class="metric__note">{{ row.note }}</div>
    </div>
  </div>
</template>

<style scoped>
.balance {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Подпись, число, полоса и доля стоят на своих местах всегда: неиспользованная строка не
   исчезает, а остаётся пустой. Иначе метрика без подписи или без доли поднималась бы вверх,
   и одинаковые по смыслу числа у разных сервисов оказывались бы на разной высоте. */
.metric__label {
  font-size: 10px;
  font-weight: 500;
  line-height: 1.3;
  height: 1.3em;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric__value {
  font-size: 20px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text);
  /* Высота слота задана в пикселях, а не в em: заглушка и ошибка печатаются мелким кеглем,
     и на `em` строка съезжала бы вверх вместе с полосой под ней. */
  line-height: 24px;
  height: 24px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* Деньги/кредиты — крупное mono-число; ошибка/заглушка — мелкий обычный текст. */
.metric__value.is-error,
.metric__value.is-na {
  font-size: 12px;
  font-weight: 500;
  font-family: inherit;
}

.metric__value.is-error { color: var(--error); }
.metric__value.is-na { color: var(--text-faint); }

/* Под баром: доля относится к нему, а не к числу над ним. */
.metric__note {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
  height: 1.4em;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-bar {
  height: 5px;
  border-radius: 3px;
  background: var(--border);
  overflow: hidden;
}

.metric-bar__fill {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: var(--accent);
  transition: width 200ms ease;
}

.metric-bar__fill.is-high { background: var(--warn); }
</style>
