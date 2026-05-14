import { reactive } from 'vue'

import { clearAuthToken, getAuthToken, setAuthToken } from './session'
import { authStatus, login as loginRequest } from './services/authService'
import type { AppSettings, AuthStatus, LoginResponse } from './types'

const state = reactive({
  token: getAuthToken(),
  authenticated: false,
  initialized: false,
  checking: false,
  user: null as AuthStatus['user'],
  status: null as AuthStatus | null,
  settings: null as AppSettings | null
})

let pendingStatus: Promise<boolean> | null = null

function applyStatus(status: AuthStatus) {
  state.status = status
  state.authenticated = status.authenticated
  state.user = status.user
}

function applySettings(settings: AppSettings) {
  state.settings = settings
  if (state.status) {
    state.status = {
      ...state.status,
      app_name: settings.app_name,
      library_subcopy: settings.library_subcopy,
      default_search_year: settings.default_search_year,
      default_search_season: settings.default_search_season,
      default_page_size: settings.default_page_size,
      default_filter_collected: settings.default_filter_collected,
      default_filter_release_tag: settings.default_filter_release_tag,
      default_filter_group_tag: settings.default_filter_group_tag,
      requires_password_change: settings.requires_password_change,
      authenticated: state.authenticated,
      user: state.user
    }
  }
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
  state.settings = null
  state.initialized = false
  await ensureStatus(true)
}

export function useAuthSession() {
  return {
    state,
    ensureStatus,
    login,
    logout,
    applySettings
  }
}
