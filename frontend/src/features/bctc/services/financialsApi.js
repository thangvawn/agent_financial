const cache = new Map()

async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload?.detail
    if (typeof detail === 'string') throw new Error(detail)
    if (detail?.message) {
      const failedTickers = Array.isArray(detail.errors)
        ? detail.errors.map((item) => item?.ticker).filter(Boolean)
        : []
      const suffix = failedTickers.length ? ` (${failedTickers.join(', ')} không tải được)` : ''
      throw new Error(`${detail.message}${suffix}`)
    }
    const message = payload?.message || `Request failed: ${response.status}`
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

export async function fetchCompanyFinancialWorkspace(
  ticker,
  { refresh = false, periodMode = 'quarter', limit = 12 } = {},
) {
  const symbol = String(ticker || '').trim().toUpperCase()
  const params = new URLSearchParams({ period_mode: periodMode, limit: String(limit) })
  if (refresh) params.set('refresh', 'true')
  return fetchWithCache(
    `company_workspace:${symbol}:${periodMode}:${limit}`,
    `/financials/${encodeURIComponent(symbol)}/company-workspace?${params.toString()}`,
    refresh,
  )
}

export async function runFinancialScenario(
  ticker,
  {
    period = '',
    revenueGrowthPct = 5,
    grossMarginPct = null,
    taxRatePct = 20,
    operatingExpenseGrowthPct = 3,
  } = {},
) {
  const symbol = String(ticker || '').trim().toUpperCase()
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/scenario`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...(period ? { period } : {}),
      revenue_growth_pct: Number(revenueGrowthPct),
      ...(grossMarginPct === null || grossMarginPct === '' ? {} : { gross_margin_pct: Number(grossMarginPct) }),
      tax_rate_pct: Number(taxRatePct),
      operating_expense_growth_pct: Number(operatingExpenseGrowthPct),
    }),
  })
  return expectJson(response)
}

export async function fetchFinancialWorkbookModel(ticker, sessionId = '') {
  const symbol = String(ticker || '').trim().toUpperCase()
  const headers = sessionId ? { 'X-Session-ID': sessionId } : undefined
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/model`, { headers })
  if (response.status === 404) return null
  return expectJson(response)
}

export async function saveFinancialWorkbookModel(ticker, model, sessionId = '') {
  const symbol = String(ticker || '').trim().toUpperCase()
  const headers = { 'Content-Type': 'application/json' }
  if (sessionId) headers['X-Session-ID'] = sessionId
  const response = await fetch(`/financials/${encodeURIComponent(symbol)}/model`, {
    method: 'POST',
    headers,
    body: JSON.stringify(model),
  })
  return expectJson(response)
}

export async function runBctcPracticeLab({ tickers = [], datasets = [], periodMode = 'quarter', period = '', limit = 12 } = {}) {
  const normalizedTickers = [...new Set((tickers || []).map((ticker) => String(ticker || '').trim().toUpperCase()).filter(Boolean))]
  if (normalizedTickers.length > 8) throw new Error('Phòng thực hành nhận tối đa 8 mã trong một lần chạy.')
  if (!['quarter', 'year'].includes(periodMode)) throw new Error('Chọn tần suất theo quý hoặc theo năm.')
  const response = await fetch('/financials/practice-lab', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tickers: normalizedTickers,
      datasets,
      period_mode: periodMode,
      ...(period ? { period } : {}),
      limit,
    }),
  })
  return expectJson(response)
}

export function clearFinancialsApiCache() {
  cache.clear()
}

export async function fetchCachedFinancialTickers() {
  return fetchWithCache('financials_cached_tickers', '/financials/cached-tickers')
}

export async function fetchCompanyMarketContext(ticker) {
  const symbol = String(ticker || '').trim().toUpperCase()
  const [prices, profile, shareholders, officers] = await Promise.allSettled([
    fetch(`/watchlist/prices/${encodeURIComponent(symbol)}`).then(expectJson),
    fetch(`/api/v1/market-portfolio/market-data/instruments/${encodeURIComponent(symbol)}/profile`).then(expectJson),
    fetch(`/api/v1/market-portfolio/market-data/instruments/${encodeURIComponent(symbol)}/shareholders`).then(expectJson),
    fetch(`/api/v1/market-portfolio/market-data/instruments/${encodeURIComponent(symbol)}/officers`).then(expectJson),
  ])
  const value = (result, fallback) => result.status === 'fulfilled' ? result.value : fallback
  return {
    prices: value(prices, { bars: [], source: 'unavailable' }),
    profile: value(profile, {}),
    shareholders: value(shareholders, {}),
    officers: value(officers, {}),
  }
}

export async function fetchFinancialQuality(ticker, { refresh = false } = {}) {
  const symbol = (ticker || '').toUpperCase().trim()
  const query = refresh ? '?refresh=1' : ''
  return fetchWithCache(`quality_${symbol}`, `/financials/${encodeURIComponent(symbol)}/quality-charts${query}`, refresh)
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

// =============================================================================
// BCTC AGENT MULTI-AGENT SYSTEM SURFACE
// =============================================================================
const BCTC_AGENT_BASE = '/api/v1/public/bctc/agent'

function getAuthHeaders(customHeaders = {}) {
  const token = typeof localStorage !== 'undefined'
    ? (localStorage.getItem('session_id') || localStorage.getItem('auth.session_id') || localStorage.getItem('public-beta.session_id'))
    : null
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function fetchBctcAgentHealth() {
  const response = await fetch(`${BCTC_AGENT_BASE}/health`)
  return expectJson(response)
}

export async function invokeBctcTool(toolId, input = {}) {
  const response = await fetch(`${BCTC_AGENT_BASE}/tools/${encodeURIComponent(toolId)}:invoke`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ input }),
  })
  return expectJson(response)
}

export async function createBctcRun({ skillId, ticker, periods = ['2024Q3'], lineItem = null, formulaId = null, query = null }) {
  const response = await fetch(`${BCTC_AGENT_BASE}/runs`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      skill_id: skillId,
      ticker,
      periods,
      line_item: lineItem,
      formula_id: formulaId,
      query,
    }),
  })
  return expectJson(response)
}

export async function getBctcRun(runId) {
  const response = await fetch(`${BCTC_AGENT_BASE}/runs/${encodeURIComponent(runId)}`, {
    headers: getAuthHeaders(),
  })
  return expectJson(response)
}

export async function createBctcMemo(memoPayload, idempotencyKey = null) {
  const customHeaders = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}
  const response = await fetch(`${BCTC_AGENT_BASE}/memos`, {
    method: 'POST',
    headers: getAuthHeaders(customHeaders),
    body: JSON.stringify(memoPayload),
  })
  return expectJson(response)
}

export async function fetchBctcMemos() {
  const response = await fetch(`${BCTC_AGENT_BASE}/memos`, {
    headers: getAuthHeaders(),
  })
  return expectJson(response)
}

export async function getBctcMemo(memoId, revisionId = null) {
  const url = revisionId
    ? `${BCTC_AGENT_BASE}/memos/${encodeURIComponent(memoId)}?revision_id=${encodeURIComponent(revisionId)}`
    : `${BCTC_AGENT_BASE}/memos/${encodeURIComponent(memoId)}`
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })
  return expectJson(response)
}

export async function deleteBctcMemo(memoId) {
  const response = await fetch(`${BCTC_AGENT_BASE}/memos/${encodeURIComponent(memoId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  return expectJson(response)
}
