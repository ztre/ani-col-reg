import { clearAuthToken, getAuthToken } from './session'
import type { Anime, AppSettings, AppSettingsUpdate, CollectionItem, LoginResponse, MaintenanceAction, PaginatedAnime, AuthStatus } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

type ApiRequestOptions = RequestInit & { skipAuth?: boolean }

async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { skipAuth = false, headers, ...rest } = options
  const token = skipAuth ? null : getAuthToken()
  const requestHeaders = new Headers(headers || undefined)

  if (rest.body) {
    requestHeaders.set('Content-Type', 'application/json')
  }
  if (token) {
    requestHeaders.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    headers: requestHeaders,
    ...rest
  })
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken()
    }
    const detail = await response.text()
    throw new Error(detail || `HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

export interface AnimeQuery {
  year?: number
  season?: number
  keyword?: string
  platform?: string
  collected?: boolean
  release_tag?: string | string[]
  group_tag?: string | string[]
  page?: number
  page_size?: number
}

export function listAnime(query: AnimeQuery): Promise<PaginatedAnime> {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== '') {
          params.append(key, String(item))
        }
      })
      return
    }
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value))
    }
  })
  return request<PaginatedAnime>(`/api/anime?${params.toString()}`)
}

export function searchAnime(query: {
  year: number
  season?: number
  keyword?: string
  page?: number
  page_size?: number
}): Promise<PaginatedAnime> {
  return request<PaginatedAnime>('/api/anime/search', {
    method: 'POST',
    body: JSON.stringify(query)
  })
}

export function getAnime(id: number): Promise<Anime> {
  return request<Anime>(`/api/anime/${id}`)
}

export function saveCollection(payload: Partial<CollectionItem> & { anime_id: number }): Promise<CollectionItem> {
  return request<CollectionItem>('/api/collection', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateCollection(id: number, payload: Partial<CollectionItem>): Promise<CollectionItem> {
  return request<CollectionItem>(`/api/collection/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function deleteCollection(id: number): Promise<CollectionItem> {
  return request<CollectionItem>(`/api/collection/${id}`, {
    method: 'DELETE'
  })
}

export function login(payload: { username: string; password: string }): Promise<LoginResponse> {
  return request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
    skipAuth: true
  })
}

export function authStatus(): Promise<AuthStatus> {
  return request<AuthStatus>('/api/auth/status', { skipAuth: false })
}

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
