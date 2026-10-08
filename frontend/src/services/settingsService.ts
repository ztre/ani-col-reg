import type { AppSettings } from '../types'

import { request } from './http'

export interface AppSettingsUpdatePayload {
  app_name?: string
  default_search_year?: number | null
  default_search_season?: number | null
  default_page_size?: number
  current_password?: string
  new_password?: string
}

export function fetchAppSettings(): Promise<AppSettings> {
  return request<AppSettings>('/api/settings')
}

export function updateAppSettings(payload: AppSettingsUpdatePayload): Promise<AppSettings> {
  return request<AppSettings>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}
