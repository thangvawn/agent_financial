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

export async function fetchFinancialUploadTypes() {
  return fetchWithCache('financial_upload_types', '/financials/upload/supported-types')
}

export async function uploadFinancialStatement({ file, ticker = '', reportType = 'auto', period = '' }) {
  const form = new FormData()
  form.set('file', file)
  if (ticker) form.set('ticker', ticker)
  if (reportType) form.set('report_type', reportType)
  if (period) form.set('period', period)
  const response = await fetch('/financials/upload', {
    method: 'POST',
    body: form,
  })
  return expectJson(response)
}

export async function analyzeFinancialStatementUpload(uploadId) {
  const response = await fetch(`/financials/uploads/${encodeURIComponent(uploadId)}/analyze`, {
    method: 'POST',
  })
  return expectJson(response)
}

export async function extractFinancialStatementUpload(uploadId) {
  const response = await fetch(`/financials/uploads/${encodeURIComponent(uploadId)}/extract`, {
    method: 'POST',
  })
  return expectJson(response)
}

export async function fetchFinancialAnalysis(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  const query = params.toString()
  return fetchWithCache(`analysis_${symbol}`, `/financials/${encodeURIComponent(symbol)}/analysis${query ? `?${query}` : ''}`, refresh)
}

export async function fetchFinancialCockpit(ticker, { refresh = false, periodType = 'quarter' } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const params = new URLSearchParams()
  if (refresh) params.set('refresh', '1')
  if (periodType) params.set('period_type', periodType)
  const query = params.toString()
  return fetchWithCache(`cockpit_${symbol}_${periodType}`, `/financials/${encodeURIComponent(symbol)}/cockpit${query ? `?${query}` : ''}`, refresh)
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

export async function submitStudentNote(payload) {
  const response = await fetch('/api/bctc/income-statement/student-notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return expectJson(response)
}

export async function fetchLineItemExplanation(itemKey, companyId, period = '', studentLevel = 'beginner') {
  const params = new URLSearchParams()
  params.set('item_key', itemKey)
  if (companyId) params.set('company_id', companyId)
  if (period) params.set('period', period)
  if (studentLevel) params.set('student_level', studentLevel)
  const query = params.toString()
  return fetchWithCache(`explain_${itemKey}_${studentLevel}`, `/api/bctc/income-statement/explain-line-item?${query}`)
}

