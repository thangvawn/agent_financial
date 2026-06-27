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
  const response = await fetch(`/api/v1/public/data-hub/instruments/${encodeURIComponent(symbol)}/history?${params}`, { signal })
  return expectJson(response)
}

export async function fetchVnUniverse() {
  const response = await fetch('/api/v1/public/data-hub/vn-market/universe')
  return expectJson(response)
}

export async function fetchVnSnapshot({ sort = 'change_desc', exchange = '', search = '', limit = 50, signal } = {}) {
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

export async function fetchNewsFeed({
  category = '',
  q = '',
  limit = 80,
  timeRangeHours = 72,
  region = '',
  sourceGroup = '',
  preset = '',
  force = false,
  sentiment = '',
  impactLevel = '',
  importance = '',
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
  if (sentiment) params.set('sentiment', sentiment)
  if (impactLevel) params.set('impact_level', impactLevel)
  if (importance) params.set('importance', importance)
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

export async function fetchArticleDetail(articleId) {
  const response = await fetch(`/api/v1/public/news/articles/${encodeURIComponent(articleId)}`)
  return expectJson(response)
}

export async function fetchNewsPulse({ category, region, sourceGroup, preset, timeRangeHours = 24 } = {}) {
  const params = new URLSearchParams({ time_range_hours: String(timeRangeHours) })
  if (category) params.set('category', category)
  if (region) params.set('region', region)
  if (sourceGroup) params.set('source_group', sourceGroup)
  if (preset) params.set('preset', preset)
  const response = await fetch(`/api/v1/public/news/pulse?${params}`)
  return expectJson(response)
}

export async function saveNewsArticle(articleId, { userId = 'anonymous', note = '' } = {}) {
  const response = await fetch(`/api/v1/public/news/articles/${encodeURIComponent(articleId)}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, note }),
  })
  return expectJson(response)
}

export async function unsaveNewsArticle(articleId, { userId = 'anonymous' } = {}) {
  const params = new URLSearchParams({ user_id: userId })
  const response = await fetch(`/api/v1/public/news/articles/${encodeURIComponent(articleId)}/save?${params}`, {
    method: 'DELETE',
  })
  return expectJson(response)
}

export async function fetchSavedNews({ userId = 'anonymous', limit = 50 } = {}) {
  const params = new URLSearchParams({ user_id: userId, limit: String(limit) })
  const response = await fetch(`/api/v1/public/news/saved?${params}`)
  return expectJson(response)
}

export async function fetchSourceHealth() {
  const response = await fetch('/api/v1/public/news/source-health')
  return expectJson(response)
}

/** Finnhub desk: economic calendar; quotes only if includeQuotes=true (saves API quota). */
export async function fetchFinnhubMacroDesk({ force = false, calendarDays = 14, includeQuotes = false } = {}) {
  const params = new URLSearchParams({
    force: String(force),
    calendar_days: String(calendarDays),
    include_quotes: String(includeQuotes),
  })
  const response = await fetch(`/api/v1/public/news/desk/finnhub?${params}`)
  return expectJson(response)
}
