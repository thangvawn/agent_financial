import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { fetchNewsHighlights } from '../../services'

const PERIODS = new Set(['day', 'week', 'month'])

function normalizePayload(payload, period) {
  const candidates = Array.isArray(payload?.items)
    ? payload.items
    : Array.isArray(payload?.highlights) ? payload.highlights : []

  return {
    ...(payload && typeof payload === 'object' ? payload : {}),
    period,
    items: candidates.filter((item) => item?.article_id).slice(0, 10),
  }
}

export default function useNewsHighlights({ initialPeriod = 'day', limit = 8 } = {}) {
  const [period, setPeriodState] = useState(PERIODS.has(initialPeriod) ? initialPeriod : 'day')
  const [payloads, setPayloads] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const periodRef = useRef(period)
  const requestRef = useRef({ sequence: 0, controller: null })

  const load = useCallback(async (targetPeriod, { force = false } = {}) => {
    requestRef.current.controller?.abort()
    const controller = new AbortController()
    const sequence = requestRef.current.sequence + 1
    requestRef.current = { sequence, controller }
    setLoading(true)
    setError('')

    try {
      const response = await fetchNewsHighlights({
        period: targetPeriod,
        limit,
        force,
        signal: controller.signal,
      })
      if (requestRef.current.sequence !== sequence) return null
      const normalized = normalizePayload(response, targetPeriod)
      setPayloads((current) => ({ ...current, [targetPeriod]: normalized }))
      return normalized
    } catch (requestError) {
      if (requestError?.name === 'AbortError' || requestRef.current.sequence !== sequence) return null
      setError(requestError?.message || 'Không thể tải tin nổi bật.')
      return null
    } finally {
      if (requestRef.current.sequence === sequence) setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    load(period)
    return () => requestRef.current.controller?.abort()
  }, [load, period])

  const setPeriod = useCallback((nextPeriod) => {
    if (PERIODS.has(nextPeriod)) {
      periodRef.current = nextPeriod
      setPeriodState(nextPeriod)
    }
  }, [])

  const refresh = useCallback(
    ({ force = true } = {}) => load(periodRef.current, { force }),
    [load],
  )

  const payload = payloads[period] || null
  const items = useMemo(() => payload?.items || [], [payload])

  return { period, setPeriod, payload, items, loading, error, refresh }
}
