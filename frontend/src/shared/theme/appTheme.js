import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useState } from 'react'

export const APP_THEME_KEY = 'public-beta.theme'
const LEGACY_THEME_KEY = 'public-beta.market-theme'
export const ThemeContext = createContext({ theme: 'dark', toggleTheme: () => {} })
export const useTheme = () => useContext(ThemeContext)

function readTheme() {
  try {
    const saved = window.localStorage.getItem(APP_THEME_KEY) ?? window.localStorage.getItem(LEGACY_THEME_KEY)
    return saved === 'light' ? 'light' : 'dark'
  }
  catch { return 'dark' }
}

// A single preference follows every workspace and migrates the former market setting.
export function useAppTheme() {
  const [theme, setTheme] = useState(readTheme)
  const toggleTheme = useCallback(() => setTheme(current => current === 'dark' ? 'light' : 'dark'), [])
  useLayoutEffect(() => { document.documentElement.dataset.theme = theme }, [theme])
  useEffect(() => {
    try { window.localStorage.setItem(APP_THEME_KEY, theme) } catch { /* Still works in memory if storage is unavailable. */ }
  }, [theme])
  useEffect(() => {
    const sync = event => {
      if (event.key === APP_THEME_KEY || event.key === null) setTheme(readTheme())
    }
    window.addEventListener('storage', sync)
    return () => window.removeEventListener('storage', sync)
  }, [])
  return useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme])
}
