import { useEffect, useState } from 'react'
import { fetchVnScreener } from '../services/dataHubApi'

export function useStockScreener({ enabled, preset, technical, sector, exchange, sort, limit, refreshTick }) {
  const selection = JSON.stringify([preset, technical, sector, exchange, sort, limit, refreshTick])
  const [navigation, setNavigation] = useState({ selection: '', cursors: [''] })
  const cursors = navigation.selection === selection ? navigation.cursors : ['']
  const cursor = cursors.at(-1)
  const key = JSON.stringify([selection, cursor, refreshTick])
  const [state, setState] = useState({ key: '', data: null, error: '', loading: false })

  useEffect(() => {
    if (!enabled) return undefined
    let cancelled = false
    const controller = new AbortController()
    let timer
    let inFlight = false
    const run = async () => {
      if (cancelled || inFlight) return
      if (document.visibilityState !== 'hidden') {
        inFlight = true
        try {
          const data = await fetchVnScreener({ preset, technical, sector, exchange, sort, limit, cursor, signal: controller.signal })
          if (!cancelled) setState({ key, data, error: '', loading: false })
        } catch (error) {
          if (!cancelled && error.name !== 'AbortError') setState({ key, data: null, error: error.message, loading: false })
        } finally { inFlight = false }
      }
      if (!cancelled) timer = window.setTimeout(run, 60_000)
    }
    const onVisible = () => { if (document.visibilityState === 'visible') { clearTimeout(timer); run() } }
    run()
    document.addEventListener('visibilitychange', onVisible)
    return () => { cancelled = true; controller.abort(); clearTimeout(timer); document.removeEventListener('visibilitychange', onVisible) }
  }, [enabled, preset, technical, sector, exchange, sort, limit, cursor, key])

  const current = state.key === key ? state : { data: null, error: '', loading: enabled }
  return { ...current, page: cursors.length,
    next: () => { if (current.data?.next_cursor) setNavigation({ selection, cursors: [...cursors, current.data.next_cursor] }) },
    previous: () => setNavigation({ selection, cursors: cursors.slice(0, -1) }),
    resetPage: () => setNavigation({ selection, cursors: [''] }),
  }
}
