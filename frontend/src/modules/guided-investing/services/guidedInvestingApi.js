async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchGuidedInvestingHome(sessionId) {
  const response = await fetch(`/api/v1/public/guided-investing/home?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function fetchGuidedMarketContext(params = {}) {
  const search = new URLSearchParams()
  if (params.usd_vnd_rate) search.set('usd_vnd_rate', params.usd_vnd_rate)
  if (params.sbv_interest_rate_pct) search.set('sbv_interest_rate_pct', params.sbv_interest_rate_pct)
  const response = await fetch(`/api/v1/public/guided-investing/market-context${search.toString() ? `?${search}` : ''}`)
  return expectJson(response)
}

export async function addGuidedWatchlistItem(body) {
  const response = await fetch('/api/v1/public/guided-investing/watchlist/items', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchGuidedWatchlist(sessionId) {
  const response = await fetch(`/api/v1/public/guided-investing/watchlist?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function reviewGuidedWatchlist(sessionId) {
  const response = await fetch(`/api/v1/public/guided-investing/watchlist/review?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  })
  return expectJson(response)
}

export async function fetchGuidedCompanyHealth(ticker) {
  const response = await fetch(`/api/v1/public/guided-investing/company/${encodeURIComponent(ticker)}`)
  return expectJson(response)
}

export async function reviewGuidedPortfolio(body) {
  const response = await fetch('/api/v1/public/guided-investing/portfolio/review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function saveGuidedPortfolio(body) {
  const response = await fetch('/api/v1/public/guided-investing/portfolio/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchGuidedSavedPortfolio(sessionId) {
  const response = await fetch(`/api/v1/public/guided-investing/portfolio?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function fetchGuidedPortfolioHistory(sessionId) {
  const response = await fetch(`/api/v1/public/guided-investing/portfolio/history?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function fetchGuidedJournal(sessionId) {
  const response = await fetch(`/api/v1/public/guided-investing/journal?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function createGuidedJournal(body) {
  const response = await fetch('/api/v1/public/guided-investing/journal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function askGuidedSafeChat(body) {
  const response = await fetch('/api/v1/public/guided-investing/safe-chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
