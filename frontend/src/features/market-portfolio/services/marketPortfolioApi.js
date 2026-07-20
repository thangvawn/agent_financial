async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

const BASE = '/api/v1/market-portfolio'

export async function fetchMpWatchlist(sessionId) {
  const params = new URLSearchParams({ session_id: sessionId })
  const response = await fetch(`${BASE}/watchlist?${params}`)
  return expectJson(response)
}

export async function addMpWatchlistItem(sessionId, symbol, label = '') {
  const response = await fetch(`${BASE}/watchlist/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, symbol, label }),
  })
  return expectJson(response)
}

export async function removeMpWatchlistItem(sessionId, symbol) {
  const params = new URLSearchParams({ session_id: sessionId })
  const response = await fetch(`${BASE}/watchlist/items/${encodeURIComponent(symbol)}?${params}`, {
    method: 'DELETE',
  })
  return expectJson(response)
}

export async function fetchMpOrders(sessionId) {
  const params = new URLSearchParams({ session_id: sessionId })
  const response = await fetch(`${BASE}/orders?${params}`)
  return expectJson(response)
}

export async function placeMpOrder(sessionId, { symbol, side, orderType, quantity, limitPrice }) {
  const response = await fetch(`${BASE}/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      symbol,
      side,
      order_type: orderType,
      quantity: Number(quantity),
      limit_price: orderType === 'LO' ? Number(limitPrice) : null,
    }),
  })
  return expectJson(response)
}

export async function cancelMpOrder(sessionId, orderId) {
  const response = await fetch(`${BASE}/orders/${encodeURIComponent(orderId)}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  })
  return expectJson(response)
}

export async function fetchMpPortfolio(sessionId) {
  const params = new URLSearchParams({ session_id: sessionId })
  const response = await fetch(`${BASE}/portfolio?${params}`)
  return expectJson(response)
}

export async function resetMpPortfolio(sessionId) {
  const response = await fetch(`${BASE}/portfolio/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  })
  return expectJson(response)
}

export async function fetchMpCompanyProfile(symbol) {
  const response = await fetch(`${BASE}/market-data/instruments/${encodeURIComponent(symbol)}/profile`)
  return expectJson(response)
}

export async function fetchMpCompanyShareholders(symbol) {
  const response = await fetch(`${BASE}/market-data/instruments/${encodeURIComponent(symbol)}/shareholders`)
  return expectJson(response)
}

export async function fetchMpDerivativesSnapshot() {
  const response = await fetch(`${BASE}/market-data/derivatives/snapshot`)
  return expectJson(response)
}

export async function fetchMpCryptoSnapshot() {
  const response = await fetch(`${BASE}/market-data/crypto/snapshot`)
  return expectJson(response)
}

export async function fetchMpCommoditiesSnapshot() {
  const response = await fetch(`${BASE}/market-data/commodities/snapshot`)
  return expectJson(response)
}

export async function fetchMpLeaders() {
  const response = await fetch(`${BASE}/market-data/leaders`)
  return expectJson(response)
}

export async function fetchMpCompanyOfficers(symbol) {
  const response = await fetch(`${BASE}/market-data/instruments/${encodeURIComponent(symbol)}/officers`)
  return expectJson(response)
}
