import { fetchInstrumentHistory } from './dataHubApi.js'
import { normalizeSparklinePoints } from './sparklineModel.js'

// One bounded queue shared by cards and table rows; failures are cached briefly.
export function createSparklineLoader(fetchHistory = fetchInstrumentHistory, { concurrency = 4, now = Date.now } = {}) {
  const cache = new Map(), pending = new Map(), queue = []
  let active = 0
  function drain() {
    while (active < concurrency && queue.length) {
      const task = queue.shift()
      active++
      Promise.resolve().then(task.run).then(task.resolve, task.reject).finally(() => { active--; drain() })
    }
  }
  return function load(symbol, { forceRefresh = false } = {}) {
    const key = String(symbol || '').trim().toUpperCase()
    if (!key) return Promise.resolve({ points: [], status: 'empty' })
    const hit = cache.get(key)
    if (!forceRefresh && hit && hit.expires > now()) return Promise.resolve(hit.result)
    if (pending.has(key)) return pending.get(key)
    const promise = new Promise((resolve, reject) => {
      queue.push({ resolve, reject, run: async () => {
        let result
        try {
          const payload = await fetchHistory(key, { period: '1mo', interval: '1d', forceRefresh })
          const points = normalizeSparklinePoints(payload?.points)
          result = { points, status: points.length >= 2 ? 'ready' : 'empty', freshness: payload?.freshness, source: payload?.source, asOf: payload?.as_of }
        } catch { result = { points: [], status: 'error' } }
        if (result.status !== 'ready' && hit?.result.points.length > 1) {
          result = { ...hit.result, freshness: 'stale', refreshFailed: true }
        }
        cache.delete(key)
        cache.set(key, { result, expires: now() + (result.status === 'ready' && !result.refreshFailed ? 300000 : 30000) })
        if (cache.size > 250) cache.delete(cache.keys().next().value)
        return result
      } })
      drain()
    }).finally(() => pending.delete(key))
    pending.set(key, promise)
    return promise
  }
}

export const loadSparklineHistory = createSparklineLoader()
