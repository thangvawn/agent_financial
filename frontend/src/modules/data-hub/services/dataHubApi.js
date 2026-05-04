async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchGlobalTerminal({ view = 'dashboard' } = {}) {
  const params = new URLSearchParams({ view })
  const response = await fetch(`/api/v1/public/data-hub/global-terminal?${params}`)
  return expectJson(response)
}

export async function fetchInstrumentHistory(symbol, { period = '6mo', interval = '1d' } = {}) {
  const params = new URLSearchParams({ period, interval })
  const response = await fetch(`/api/v1/public/data-hub/instruments/${encodeURIComponent(symbol)}/history?${params}`)
  return expectJson(response)
}

export async function fetchDataHubTopics() {
  const response = await fetch('/api/v1/public/data-hub/topics')
  return expectJson(response)
}

export async function fetchNewsFeed({
  category = '',
  q = '',
  limit = 80,
  timeRangeHours = 72,
  region = '',
  sourceGroup = '',
  preset = '',
  force = false,
} = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    time_range_hours: String(timeRangeHours),
    force: String(force),
  })
  if (category) params.set('category', category)
  if (q) params.set('q', q)
  if (region) params.set('region', region)
  if (sourceGroup) params.set('source_group', sourceGroup)
  if (preset) params.set('preset', preset)
  const response = await fetch(`/api/v1/public/news/feed?${params}`)
  return expectJson(response)
}

export async function askNewsAnalyst(body) {
  const response = await fetch('/api/v1/public/news/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
