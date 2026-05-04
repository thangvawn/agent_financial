async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchMarketOverviewHistory() {
  const response = await fetch('/dashboard/history')
  return expectJson(response)
}

export async function fetchMarketOverviewCrossAsset(limit = 180) {
  const response = await fetch(`/dashboard/cross-asset?limit=${encodeURIComponent(limit)}`)
  return expectJson(response)
}
