async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchInsightsHome({
  sessionId,
  level = '',
  ticker = 'FPT',
  usdVndRate = '',
  sbvInterestRatePct = '',
}) {
  const params = new URLSearchParams()
  if (sessionId) params.set('session_id', sessionId)
  if (level) params.set('level', level)
  if (ticker) params.set('ticker', ticker)
  if (usdVndRate !== '' && usdVndRate !== null && usdVndRate !== undefined) params.set('usd_vnd_rate', String(usdVndRate))
  if (sbvInterestRatePct !== '' && sbvInterestRatePct !== null && sbvInterestRatePct !== undefined) {
    params.set('sbv_interest_rate_pct', String(sbvInterestRatePct))
  }
  const response = await fetch(`/api/v1/public/insights/home?${params.toString()}`)
  return expectJson(response)
}

export async function fetchInsightsDashboard({
  sessionId,
  userMode = 'investor',
  range = '1M',
} = {}) {
  const params = new URLSearchParams()
  if (sessionId) params.set('session_id', sessionId)
  if (userMode) params.set('user_mode', userMode)
  if (range) params.set('range', range)

  const response = await fetch(`/api/v1/public/insights/dashboard?${params.toString()}`)
  return expectJson(response)
}
