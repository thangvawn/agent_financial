async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchGlobalTerminal({ view = 'dashboard', signal } = {}) {
  const params = new URLSearchParams({ view })
  const response = await fetch(`/api/v1/public/data-hub/global-terminal?${params}`, { signal })
  return expectJson(response)
}

export async function fetchInstrumentHistory(symbol, { period = '6mo', interval = '1d', signal } = {}) {
  const params = new URLSearchParams({ period, interval })
  const response = await fetch(`/api/v1/public/data-hub/instruments/${encodeURIComponent(symbol)}/history?${params}`, {
    signal,
  })
  return expectJson(response)
}

export async function fetchVnUniverse() {
  const response = await fetch('/api/v1/public/data-hub/vn-market/universe')
  return expectJson(response)
}

export async function fetchVnSnapshot({ sort = 'market_cap_desc', exchange = '', search = '', limit = 50, signal } = {}) {
  const params = new URLSearchParams({ sort, limit: String(limit) })
  if (exchange) params.set('exchange', exchange)
  if (search) params.set('search', search)
  const response = await fetch(`/api/v1/public/data-hub/vn-market/snapshot?${params}`, { signal })
  return expectJson(response)
}

export async function fetchDataHubTopics() {
  const response = await fetch('/api/v1/public/data-hub/topics')
  return expectJson(response)
}
