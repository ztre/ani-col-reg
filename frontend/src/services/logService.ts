import type { PaginatedAppLogs } from '../types'

import { buildSearchParams, request } from './http'

export interface LogQuery {
  level?: string
  source?: string
  limit?: number
  offset?: number
}

export function fetchLogs(params: LogQuery): Promise<PaginatedAppLogs> {
  const search = buildSearchParams(params)
  return request<PaginatedAppLogs>(`/api/logs?${search.toString()}`)
}
