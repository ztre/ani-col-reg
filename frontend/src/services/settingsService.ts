import type { AppSettings, AppSettingsUpdate, CollectionResetAction, MaintenanceAction } from '../types'

import { request } from './http'

export function getSettings(): Promise<AppSettings> {
  return request<AppSettings>('/api/settings')
}

export function updateSettings(payload: AppSettingsUpdate): Promise<AppSettings> {
  return request<AppSettings>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export function clearCoverCache(): Promise<MaintenanceAction> {
  return request<MaintenanceAction>('/api/settings/maintenance/clear-cover-cache', {
    method: 'POST'
  })
}

export function resetCollectionData(): Promise<CollectionResetAction> {
  return request<CollectionResetAction>('/api/settings/maintenance/reset-collection-data', {
    method: 'POST'
  })
}