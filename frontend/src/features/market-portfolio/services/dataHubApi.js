const clientHistoryCache = new Map()
const inflightHistory = new Map()

const clientTerminalCache = new Map()
const inflightTerminal = new Map()

const clientSnapshotCache = new Map()
const inflightSnapshot = new Map()

function getHistoryTtl(interval) {
  const norm = (interval || '1d').toLowerCase()
  if (norm === '1m') return 15_000
  if (['5m', '15m', '30m'].includes(norm)) return 30_000
  if (['1h', '4h'].includes(norm)) return 90_000
  return 300_000 // 5 minutes for daily / weekly
}

export function clearDataHubClientCache() {
  clientHistoryCache.clear()
  clientTerminalCache.clear()
  clientSnapshotCache.clear()
}

async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchGlobalTerminal({ view = 'dashboard', refresh = false, signal } = {}) {
  const key = view || 'dashboard'
  const now = Date.now()
  const cached = clientTerminalCache.get(key)
  if (!refresh && cached && (now - cached.ts) < 20_000) {
    return cached.data
  }
  if (inflightTerminal.has(key)) {
    return inflightTerminal.get(key)
  }

  const promise = (async () => {
    try {
      const params = new URLSearchParams({ view })
      if (refresh) params.set('refresh', 'true')
      const response = await fetch(`/api/v1/public/data-hub/global-terminal?${params}`, {
        signal,
        cache: 'no-store',
        headers: { Accept: 'application/json' },
      })
      const data = await expectJson(response)
      if (data) {
        clientTerminalCache.set(key, { data, ts: Date.now() })
      }
      return data
    } finally {
      inflightTerminal.delete(key)
    }
  })()

  inflightTerminal.set(key, promise)
  return promise
}

export async function fetchInstrumentHistory(symbol, { period = '6mo', interval = '1d', signal, forceRefresh = false } = {}) {
  const key = `${(symbol || '').toUpperCase()}:${period}:${interval}`
  const now = Date.now()
  const cached = clientHistoryCache.get(key)
  const ttl = getHistoryTtl(interval)

  if (!forceRefresh && cached && (now - cached.ts) < ttl) {
    return cached.data
  }

  if (inflightHistory.has(key)) {
    return inflightHistory.get(key)
  }

  const promise = (async () => {
    try {
      const params = new URLSearchParams({ period, interval })
      const response = await fetch(`/api/v1/public/data-hub/instruments/${encodeURIComponent(symbol)}/history?${params}`, {
        signal,
        cache: 'no-store',
        headers: { Accept: 'application/json' },
      })
      const data = await expectJson(response)
      if (data && Array.isArray(data.points) && data.points.length > 0) {
        clientHistoryCache.set(key, { data, ts: Date.now() })
      }
      return data
    } finally {
      inflightHistory.delete(key)
    }
  })()

  inflightHistory.set(key, promise)
  return promise
}

export async function fetchVnUniverse() {
  const response = await fetch('/api/v1/public/data-hub/vn-market/universe')
  return expectJson(response)
}

export async function fetchVnSnapshot({ sort = 'market_cap_desc', exchange = '', search = '', limit = 50, refresh = false, signal } = {}) {
  const key = `${sort}:${exchange}:${search}:${limit}`
  const now = Date.now()
  const cached = clientSnapshotCache.get(key)
  if (!refresh && cached && (now - cached.ts) < 15_000) {
    return cached.data
  }
  if (inflightSnapshot.has(key)) {
    return inflightSnapshot.get(key)
  }

  const promise = (async () => {
    try {
      const params = new URLSearchParams({ sort, limit: String(limit) })
      if (exchange) params.set('exchange', exchange)
      if (search) params.set('search', search)
      if (refresh) params.set('refresh', 'true')
      const response = await fetch(`/api/v1/public/data-hub/vn-market/snapshot?${params}`, {
        signal,
        cache: 'no-store',
        headers: { Accept: 'application/json' },
      })
      const data = await expectJson(response)
      if (data) {
        clientSnapshotCache.set(key, { data, ts: Date.now() })
      }
      return data
    } finally {
      inflightSnapshot.delete(key)
    }
  })()

  inflightSnapshot.set(key, promise)
  return promise
}

export async function fetchDataHubTopics() {
  const response = await fetch('/api/v1/public/data-hub/topics')
  return expectJson(response)
}
