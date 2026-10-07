import { reactive } from 'vue'

import { clearAuthToken, getAuthToken, setAuthToken } from './session'
import { authStatus, login as loginRequest } from './services/authService'
import type { AuthStatus, LoginResponse } from './types'

const state = reactive({
  token: getAuthToken(),
  authenticated: false,
  initialized: false,
  checking: false,
  user: null as AuthStatus['user'],
  status: null as AuthStatus | null
})

let pendingStatus: Promise<boolean> | null = null

function applyStatus(status: AuthStatus) {
  state.status = status
  state.authenticated = status.authenticated
  state.user = status.user
}

async function ensureStatus(force = false) {
  if (state.initialized && !force) {
    return state.authenticated
  }
  if (pendingStatus && !force) {
    return pendingStatus
  }

  state.checking = true
  pendingStatus = authStatus()
    .then((status) => {
      if (!status.authenticated) {
        clearAuthToken()
        state.token = null
      } else {
        state.token = getAuthToken()
      }
      applyStatus(status)
      state.initialized = true
      return status.authenticated
    })
    .finally(() => {
      pendingStatus = null
      state.checking = false
    })

  return pendingStatus
}

async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await loginRequest({ username, password })
  setAuthToken(response.token)
  state.token = response.token
  state.initialized = true
  applyStatus(response.status)
  return response
}

async function logout() {
  clearAuthToken()
  state.token = null
  state.authenticated = false
  state.user = null
  state.initialized = false
  await ensureStatus(true)
}

export function useAuthSession() {
  return {
    state,
    ensureStatus,
    login,
    logout
  }
}
