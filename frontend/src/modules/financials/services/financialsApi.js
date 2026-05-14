async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchFinancialStatus() {
  const response = await fetch('/financials/status')
  return expectJson(response)
}

export async function fetchFinancialAnalysis(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/analysis${query ? `?${query}` : ''}`)
  return expectJson(response)
}

export async function fetchFinancialSections(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/sections${query ? `?${query}` : ''}`)
  return expectJson(response)
}

export async function fetchFinancialSection(ticker, section, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const normalizedSection = (section || '').trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/sections/${encodeURIComponent(normalizedSection)}${query ? `?${query}` : ''}`)
  return expectJson(response)
}

export async function fetchFinancialQualityCharts(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/quality-charts${query ? `?${query}` : ''}`)
  return expectJson(response)
}

export async function fetchBalanceSheetStrength(ticker, { period = '', refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (period) params.set('period', period)
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/balance-sheet-strength${query ? `?${query}` : ''}`)
  return expectJson(response)
}

export async function fetchFinancialPeers(ticker, peers = '') {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if ((peers || '').trim()) params.set('peers', peers)
  const query = params.toString()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/peers${query ? `?${query}` : ''}`)
  return expectJson(response)
}
