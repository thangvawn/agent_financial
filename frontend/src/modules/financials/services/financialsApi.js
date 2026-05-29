const cache = new Map()

async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

async function fetchWithCache(key, url, refresh = false) {
  if (!refresh && cache.has(key)) return cache.get(key)
  const response = await fetch(url)
  const payload = await expectJson(response)
  cache.set(key, payload)
  return payload
}

export async function fetchFinancialStatus() {
  return fetchWithCache('status', '/financials/status')
}

export async function fetchFinancialAnalysis(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  return fetchWithCache(`analysis_${symbol}`, `/financials/${encodeURIComponent(symbol)}/analysis${query ? `?${query}` : ''}`, refresh)
}

export async function fetchFinancialSections(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  return fetchWithCache(`sections_${symbol}`, `/financials/${encodeURIComponent(symbol)}/sections${query ? `?${query}` : ''}`, refresh)
}

export async function fetchFinancialSection(ticker, section, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const normalizedSection = (section || '').trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  return fetchWithCache(`section_${symbol}_${normalizedSection}`, `/financials/${encodeURIComponent(symbol)}/sections/${encodeURIComponent(normalizedSection)}${query ? `?${query}` : ''}`, refresh)
}

export async function fetchFinancialQualityCharts(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  return fetchWithCache(`quality_${symbol}`, `/financials/${encodeURIComponent(symbol)}/quality-charts${query ? `?${query}` : ''}`, refresh)
}

export async function fetchBalanceSheetStrength(ticker, { period = '', refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (period) params.set('period', period)
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  return fetchWithCache(`balance_${symbol}_${period}`, `/financials/${encodeURIComponent(symbol)}/balance-sheet-strength${query ? `?${query}` : ''}`, refresh)
}

export async function fetchFinancialPeers(ticker, peers = '') {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if ((peers || '').trim()) params.set('peers', peers)
  const query = params.toString()
  return fetchWithCache(`peers_${symbol}_${peers}`, `/financials/${encodeURIComponent(symbol)}/peers${query ? `?${query}` : ''}`)
}
