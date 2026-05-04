async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

function headers(adminKey) {
  return {
    'Content-Type': 'application/json',
    'X-Admin-Analytics-Key': adminKey || '',
  }
}

export async function fetchAnalyticsStatus(adminKey) {
  return expectJson(await fetch('/admin/analytics/status', { headers: headers(adminKey) }))
}

export async function fetchAnalyticsKpis(adminKey, window = 'day') {
  return expectJson(await fetch(`/admin/analytics/kpis?window=${encodeURIComponent(window)}`, { headers: headers(adminKey) }))
}

export async function fetchAnalyticsDashboard(adminKey, kind, window = 'day') {
  const suffix = kind === 'product' ? `?window=${encodeURIComponent(window)}` : ''
  return expectJson(await fetch(`/admin/analytics/dashboards/${encodeURIComponent(kind)}${suffix}`, { headers: headers(adminKey) }))
}

export async function fetchAnalyticsEvents(adminKey, filters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  })
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return expectJson(await fetch(`/admin/analytics/events${suffix}`, { headers: headers(adminKey) }))
}

export async function fetchAnalyticsOps(adminKey, kind) {
  return expectJson(await fetch(`/admin/analytics/ops/${encodeURIComponent(kind)}`, { headers: headers(adminKey) }))
}

export async function fetchAnalyticsAlerts(adminKey, status = '') {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : ''
  return expectJson(await fetch(`/admin/analytics/alerts${suffix}`, { headers: headers(adminKey) }))
}

export async function runAnalyticsKpiRollup(adminKey, window_grain = 'day') {
  return expectJson(
    await fetch('/admin/analytics/jobs/run-kpi-rollup', {
      method: 'POST',
      headers: headers(adminKey),
      body: JSON.stringify({ window_grain }),
    })
  )
}

export async function runAnalyticsOpsSnapshot(adminKey, window_hours = 24) {
  return expectJson(
    await fetch('/admin/analytics/jobs/run-ops-snapshot', {
      method: 'POST',
      headers: headers(adminKey),
      body: JSON.stringify({ window_hours }),
    })
  )
}

export async function evaluateAnalyticsAlerts(adminKey, force_reopen = false) {
  return expectJson(
    await fetch('/admin/analytics/jobs/evaluate-alerts', {
      method: 'POST',
      headers: headers(adminKey),
      body: JSON.stringify({ force_reopen }),
    })
  )
}
