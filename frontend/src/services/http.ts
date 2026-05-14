import { clearAuthToken, getAuthToken } from '../session'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export type ApiRequestOptions = RequestInit & { skipAuth?: boolean }

export async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
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

export function buildSearchParams(query: object) {
  const params = new URLSearchParams()

  Object.entries(query as Record<string, unknown>).forEach(([key, value]) => {
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

  return params
}