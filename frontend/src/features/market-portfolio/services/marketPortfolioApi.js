import { authenticatedFetch } from '../../auth/services/sessionClient'
async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

const BASE = '/api/v1/market-portfolio'

export async function fetchMpWatchlist(sessionId, { signal } = {}) {
  const response = await authenticatedFetch(`${BASE}/watchlist`, { signal }, sessionId)
  return expectJson(response)
}

export async function fetchMpWatchlistInstruments(sessionId, { signal } = {}) {
  return expectJson(await authenticatedFetch(`${BASE}/watchlist/instruments`, { signal }, sessionId))
}

export async function addMpWatchlistItem(sessionId, symbol, label = '') {
  const response = await authenticatedFetch(`${BASE}/watchlist/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, symbol, label }),
  }, sessionId)
  return expectJson(response)
}

export async function removeMpWatchlistItem(sessionId, symbol) {
  const response = await authenticatedFetch(`${BASE}/watchlist/items/${encodeURIComponent(symbol)}`, {
    method: 'DELETE',
  }, sessionId)
  return expectJson(response)
}

export async function fetchMpOrders(sessionId) {
  const response = await authenticatedFetch(`${BASE}/orders`, {}, sessionId)
  return expectJson(response)
}

export async function placeMpOrder(sessionId, { symbol, side, orderType, quantity, limitPrice }) {
  const response = await authenticatedFetch(`${BASE}/orders`, {
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
  }, sessionId)
  return expectJson(response)
}

export async function cancelMpOrder(sessionId, orderId) {
  const response = await authenticatedFetch(`${BASE}/orders/${encodeURIComponent(orderId)}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  }, sessionId)
  return expectJson(response)
}

export async function fetchMpPortfolio(sessionId) {
  const response = await authenticatedFetch(`${BASE}/portfolio`, {}, sessionId)
  return expectJson(response)
}

export async function resetMpPortfolio(sessionId) {
  const response = await authenticatedFetch(`${BASE}/portfolio/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  }, sessionId)
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

export async function fetchMpCryptoSnapshot({ signal } = {}) {
  const response = await fetch(`${BASE}/market-data/crypto/snapshot`, {
    signal,
    cache: 'no-store',
    headers: { Accept: 'application/json' },
  })
  return expectJson(response)
}

export async function fetchMpCommoditiesSnapshot({ signal, refresh = false } = {}) {
  const response = await fetch(`${BASE}/market-data/commodities/snapshot${refresh ? '?refresh=true' : ''}`, { signal, cache: 'no-store' })
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
