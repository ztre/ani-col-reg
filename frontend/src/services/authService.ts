import type { AuthStatus, LoginResponse } from '../types'

import { request } from './http'

export function login(payload: { username: string; password: string }): Promise<LoginResponse> {
  return request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
    skipAuth: true
  })
}

export function authStatus(): Promise<AuthStatus> {
  return request<AuthStatus>('/api/auth/status')
}