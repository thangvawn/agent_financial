import { useEffect, useRef, useState } from 'react'
import { fetchInstrumentHistory } from '../services/dataHubApi'
import { normalizeCommodityHistory } from '../services/commodityModel'

const EMPTY = { points: [], status: 'loading', loading: true }
const POLL_MS = 300_000

export function useCommodityHistory(symbol, period, revision) {
  const [result, setResult] = useState(null)
  const previousRevision = useRef(revision)
  const key = `${symbol}:${period}`
  useEffect(() => {
    let cancelled = false, busy = false
    if (!symbol) return
    const keepPrevious = (previous, error) => previous?.key === key && previous.points.length > 1
      ? { ...previous, loading: false, freshness: 'stale', error }
      : { key, points: [], status: 'error', loading: false, error }
    async function load(forceRefresh = false) {
      if (busy || document.visibilityState === 'hidden') return
      busy = true
      setResult(previous => previous?.key === key ? { ...previous, loading: true } : { ...EMPTY, key })
      try {
        // Shared request has its own timeout; unmount must not abort another consumer.
        const payload = await fetchInstrumentHistory(symbol, { period, interval: '1d', forceRefresh })
        if (cancelled) return
        const points = normalizeCommodityHistory(payload?.points)
        const error = payload?.refresh_status === 'failed' ? 'Chưa làm mới được lịch sử; đang giữ dữ liệu trước đó.' : ''
        setResult(previous => {
          if (points.length < 2 && previous?.key === key && previous.points.length > 1) {
            return keepPrevious(previous, 'Nguồn chưa trả đủ lịch sử; đang giữ dữ liệu trước đó.')
          }
          return { key, points, status: points.length > 1 ? 'ready' : 'empty', loading: false,
            freshness: payload?.freshness, source: payload?.source, asOf: payload?.as_of, error,
            notice: payload?.refresh_status === 'throttled' ? 'Vừa yêu cầu cập nhật. Có thể thử lại sau vài giây.' : '' }
        })
      } catch {
        if (!cancelled) setResult(previous => keepPrevious(previous, 'Chưa làm mới được lịch sử; đang giữ dữ liệu trước đó.'))
      } finally { busy = false }
    }
    const forced = previousRevision.current !== revision
    previousRevision.current = revision
    load(forced)
    const timer = setInterval(() => load(), POLL_MS)
    const resume = () => load()
    window.addEventListener('focus', resume)
    window.addEventListener('online', resume)
    document.addEventListener('visibilitychange', resume)
    return () => {
      cancelled = true
      clearInterval(timer)
      window.removeEventListener('focus', resume)
      window.removeEventListener('online', resume)
      document.removeEventListener('visibilitychange', resume)
    }
  }, [key, symbol, period, revision])
  return result?.key === key ? result : EMPTY
}
