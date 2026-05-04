async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(message)
  }
  return payload
}

export async function submitFinancialHealthAssessment(body) {
  const response = await fetch('/api/v1/public/financial-health/assessment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchFinancialHealthSnapshot(sessionId) {
  const response = await fetch(`/api/v1/public/financial-health?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function askFinancialHealthCoach(sessionId, focus) {
  const response = await fetch(
    `/api/v1/public/financial-health/coach?session_id=${encodeURIComponent(sessionId)}&focus=${encodeURIComponent(focus)}`,
    { method: 'POST' },
  )
  return expectJson(response)
}
