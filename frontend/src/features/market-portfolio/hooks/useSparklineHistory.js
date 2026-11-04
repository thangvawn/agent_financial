import { useEffect, useRef, useState } from 'react'
import { loadSparklineHistory } from '../services/sparklineHistory'

export function useSparklineHistory(symbol, { refreshToken = 0, pollMs = 0 } = {}) {
  const elementRef = useRef(null)
  const [result, setResult] = useState(null)
  useEffect(() => {
    let cancelled = false, busy = false, visible = false, force = refreshToken !== 0
    const load = async () => {
      if (busy || !visible || document.visibilityState === 'hidden') return
      busy = true
      const data = await loadSparklineHistory(symbol, { forceRefresh: force })
      force = false
      if (!cancelled) setResult({ symbol, ...data })
      busy = false
    }
    const observer = typeof IntersectionObserver === 'undefined' ? null : new IntersectionObserver(entries => {
      visible = entries.some(entry => entry.isIntersecting)
      if (visible) load()
    }, { rootMargin: '80px' })
    if (observer && elementRef.current) observer.observe(elementRef.current)
    else { visible = true; load() }
    const timer = pollMs ? setInterval(load, pollMs) : null
    if (pollMs) {
      window.addEventListener('focus', load)
      window.addEventListener('online', load)
      document.addEventListener('visibilitychange', load)
    }
    return () => {
      cancelled = true
      observer?.disconnect()
      clearInterval(timer)
      window.removeEventListener('focus', load)
      window.removeEventListener('online', load)
      document.removeEventListener('visibilitychange', load)
    }
  }, [symbol, refreshToken, pollMs])
  return { elementRef, ...(result?.symbol === symbol ? result : { status: 'loading', points: [] }) }
}
