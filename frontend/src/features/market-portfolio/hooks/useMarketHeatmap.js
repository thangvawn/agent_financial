import { useCallback, useEffect, useState } from 'react'

export default function useMarketHeatmap() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)
  const refresh = useCallback(() => { setLoading(true); setVersion(v => v + 1) }, [])
  useEffect(() => {
    const controller = new AbortController()
    let stopped = false, busy = false, timer
    async function load() {
      if (busy || stopped) return
      if (document.hidden) { timer = setTimeout(load, 30000); return }
      busy = true
      let interval = 30000
      try {
        const response = await fetch('/api/v1/public/data-hub/vn-market/heatmap', { signal: controller.signal, cache: 'no-store' })
        if (!response.ok) throw new Error('Không tải được bản đồ thị trường. Vui lòng thử lại.')
        const result = await response.json()
        if (!Array.isArray(result.items)) throw new Error('Dữ liệu bản đồ chưa hợp lệ.')
        interval = Math.max(30, result.refresh_interval_seconds || 30) * 1000
        if (!stopped) { setData(result); setError('') }
      } catch (e) { if (!stopped && e.name !== 'AbortError') setError(e.message) }
      finally {
        if (!stopped) { setLoading(false); timer = setTimeout(load, interval) }
        busy = false
      }
    }
    const visible = () => { if (!document.hidden) { clearTimeout(timer); load() } }
    load()
    document.addEventListener('visibilitychange', visible)
    return () => { stopped = true; controller.abort(); clearTimeout(timer); document.removeEventListener('visibilitychange', visible) }
  }, [version])
  return { data, error, loading, refresh }
}
