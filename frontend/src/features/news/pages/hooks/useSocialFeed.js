import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchSocialFeed, socialRequest } from '../../services/socialApi'

export function socialFilters(search = '') {
  const p = new URLSearchParams(search)
  const pick = (name, choices, fallback) => choices.includes(p.get(name)) ? p.get(name) : fallback
  return { market: pick('market', ['all', 'vietnam', 'global'], 'all'),
    platform: pick('platform', ['all', 'youtube', 'reddit'], 'all'),
    scope: pick('scope', ['all', 'watchlist', 'saved'], 'all'),
    hours: pick('hours', ['24', '168'], '168'), q: (p.get('q') || '').slice(0, 120) }
}

export default function useSocialFeed(sessionId) {
  const [filters, setFilters] = useState(() => socialFilters(window.location.search))
  const [data, setData] = useState(null)
  const [sourceData, setSourceData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [sourceError, setSourceError] = useState('')
  const [version, setVersion] = useState(0)
  const [pending, setPending] = useState(false)
  const generation = useRef(0)
  const moreBusy = useRef(false)
  const changedJob = useRef('')
  const dataRef = useRef(null)
  dataRef.current = data
  const scopeKey = JSON.stringify(filters)
  const activeData = data?.scopeKey === scopeKey ? data : null
  const refresh = useCallback(() => { setPending(false); setVersion(n => n + 1) }, [])
  const updateFilters = useCallback(patch => {
    setFilters(previous => {
      const next = { ...previous, ...patch }
      const url = new URL(window.location.href)
      for (const [key, value] of Object.entries(next)) {
        if (value) url.searchParams.set(key, value)
        else url.searchParams.delete(key)
      }
      window.history.replaceState(window.history.state, '', url)
      return next
    })
  }, [])

  useEffect(() => {
    const onPop = () => setFilters(socialFilters(window.location.search))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const id = ++generation.current
    moreBusy.current = false
    setLoading(true); setError(''); setLoadingMore(false); setPending(false)
    const timer = setTimeout(() => {
      fetchSocialFeed(sessionId, JSON.parse(scopeKey), { signal: controller.signal })
        .then(result => { if (id === generation.current) setData({ ...result, scopeKey, pages: 1 }) })
        .catch(e => { if (e.name !== 'AbortError' && id === generation.current) setError(e.message) })
        .finally(() => { if (id === generation.current) setLoading(false) })
    }, 250)
    return () => { clearTimeout(timer); controller.abort(); generation.current++ }
  }, [sessionId, scopeKey, version])

  const loadMore = useCallback(async () => {
    if (moreBusy.current || !activeData?.next_cursor || loading) return
    const id = generation.current
    moreBusy.current = true; setLoadingMore(true); setError('')
    try {
      const result = await fetchSocialFeed(sessionId, filters, { cursor: activeData.next_cursor })
      if (id === generation.current) setData(previous => ({ ...result, scopeKey, pages: previous.pages + 1,
        topics: [...previous.topics, ...result.topics.filter(t => !previous.topics.some(p => p.id === t.id))] }))
    } catch (e) {
      if (id === generation.current) {
        if (e.status === 410) refresh()
        else setError(e.message)
      }
    } finally {
      if (id === generation.current) { moreBusy.current = false; setLoadingMore(false) }
    }
  }, [sessionId, filters, scopeKey, activeData, loading, refresh])

  useEffect(() => {
    let stopped = false
    let busy = false
    const controller = new AbortController()
    async function poll() {
      if (busy || document.hidden) return
      busy = true
      try {
        const result = await socialRequest('/sources', sessionId, { signal: controller.signal })
        if (stopped) return
        setSourceData(result); setSourceError('')
        const signature = JSON.stringify(result.jobs.filter(j => ['succeeded', 'failed', 'cancelled'].includes(j.status)).map(j => [j.id, j.updated_at]))
        if (changedJob.current && changedJob.current !== signature) {
          if (dataRef.current?.pages > 1) setPending(true)
          else refresh()
        }
        changedJob.current = signature
      } catch (e) {
        if (!stopped && e.name !== 'AbortError') setSourceError(e.message)
      } finally { busy = false }
    }
    poll()
    const timer = setInterval(poll, 10000)
    window.addEventListener('focus', poll)
    document.addEventListener('visibilitychange', poll)
    return () => { stopped = true; controller.abort(); clearInterval(timer); window.removeEventListener('focus', poll); document.removeEventListener('visibilitychange', poll) }
  }, [sessionId, refresh, version])

  return { filters, updateFilters, data: activeData, sourceData, loading, loadingMore, error,
    sourceError, pending, refresh, loadMore }
}
