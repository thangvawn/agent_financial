async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

const NEWS_HIGHLIGHT_PERIODS = new Set(['day', 'week', 'month'])

export async function fetchNewsHighlights({ period = 'day', limit = 8, force = false, signal } = {}) {
  if (!NEWS_HIGHLIGHT_PERIODS.has(period)) {
    throw new Error('Unsupported news highlight period')
  }
  if (!Number.isInteger(limit) || limit < 5 || limit > 10) {
    throw new Error('News highlight limit must be between 5 and 10')
  }

  const params = new URLSearchParams({
    period,
    limit: String(limit),
    force: String(Boolean(force)),
  })
  const response = await fetch(`/api/v1/public/news/highlights?${params}`, { signal })
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
  signal,
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
  const response = await fetch(`/api/v1/public/news/feed?${params}`, { signal })
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

export async function fetchFinnhubMacroDesk({ force = false, calendarDays = 14, includeQuotes = false } = {}) {
  const params = new URLSearchParams({
    force: String(force),
    calendar_days: String(calendarDays),
    include_quotes: String(includeQuotes),
  })
  const response = await fetch(`/api/v1/public/news/desk/finnhub?${params}`)
  return expectJson(response)
}
