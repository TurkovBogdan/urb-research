import { internalApi } from '@/api/client/internal'

const BASE = '/tasks'

export interface TaskStats24h {
  total: number
  success: number
  error: number
  running: number
}

export interface TaskInfo {
  module: string
  code: string
  name: string
  description: string
  schedule: string | null
  ttl: number
  enabled: boolean
  user_request: boolean
  sort: number
  stats_24h: TaskStats24h
}

export interface TaskRunInfo {
  id: number
  status: 'running' | 'success' | 'error'
  started_at: string
  finished_at: string | null
  heartbeat_at: string | null
  error_text: string | null
  payload: Record<string, unknown> | null
}

export interface TaskRunLog {
  id: number
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  created_at: string
}

export interface TaskRunsPage {
  items: TaskRunInfo[]
  total: number
}

export async function fetchTasks(): Promise<TaskInfo[]> {
  return internalApi.get<TaskInfo[]>(BASE)
}

export async function fetchTask(module: string, code: string): Promise<TaskInfo> {
  return internalApi.get<TaskInfo>(`${BASE}/${module}/${code}`)
}

export async function fetchTaskRuns(
  module: string,
  code: string,
  opts: {
    limit?: number
    offset?: number
    status?: TaskRunInfo['status'] | null
    sortBy?: string
    sortDir?: 'asc' | 'desc'
  } = {},
): Promise<TaskRunsPage> {
  return internalApi.get<TaskRunsPage>(`${BASE}/${module}/${code}/runs`, {
    query: {
      limit: opts.limit ?? 25,
      offset: opts.offset ?? 0,
      status: opts.status ?? null,
      sort_by: opts.sortBy ?? null,
      sort_dir: opts.sortDir ?? null,
    },
  })
}

export async function fetchTaskRunLogs(
  module: string,
  code: string,
  runId: number,
): Promise<TaskRunLog[]> {
  return internalApi.get<TaskRunLog[]>(`${BASE}/${module}/${code}/runs/${runId}/logs`)
}
