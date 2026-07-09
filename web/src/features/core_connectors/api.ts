import { internalApi } from '@/api/client/internal'

const BASE = '/connectors'

// Паспорт коннектора.
export interface ConnectorInfo {
  service: string
  name: string
  description: string
  enabled: boolean
  has_balance: boolean
}

// Одна метрика баланса: денежная величина ИЛИ «использовано из всего».
export interface BalanceMetric {
  label: string
  amount: number | null
  currency: string | null
  used: number | null
  total: number | null
  used_percent: number | null
  unit: string | null
}

// Баланс коннектора: набор доступных метрик (баланс, лимит ключа, кредиты…). error — если не сняли.
export interface ConnectorBalance {
  service: string
  name: string
  metrics: BalanceMetric[]
  error: string | null
}

// Паспорт + опциональный баланс.
export interface ConnectorView {
  info: ConnectorInfo
  balance: ConnectorBalance | null
}

export async function fetchConnectors(): Promise<ConnectorView[]> {
  return internalApi.get<ConnectorView[]>(BASE)
}
