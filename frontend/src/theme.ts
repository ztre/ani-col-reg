import { computed, ref } from 'vue'

export type ThemeMode = 'dark' | 'light'

const STORAGE_KEY = 'ani-col-reg.theme-mode'
const themeMode = ref<ThemeMode>('dark')

function resolveInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  const saved = window.localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') {
    return saved
  }

  return 'dark'
}

function applyTheme(mode: ThemeMode) {
  if (typeof document === 'undefined') {
    return
  }

  document.documentElement.dataset.theme = mode
}

export function initializeThemeMode() {
  const initial = resolveInitialTheme()
  themeMode.value = initial
  applyTheme(initial)
}

export function useThemeMode() {
  const isLight = computed(() => themeMode.value === 'light')

  function setTheme(mode: ThemeMode) {
    themeMode.value = mode
    applyTheme(mode)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, mode)
    }
  }

  function toggleTheme() {
    setTheme(themeMode.value === 'dark' ? 'light' : 'dark')
  }

  return {
    themeMode,
    isLight,
    setTheme,
    toggleTheme,
  }
}