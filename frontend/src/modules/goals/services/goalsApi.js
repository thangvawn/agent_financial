async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(message)
  }
  return payload
}

export async function listGoals(sessionId) {
  const response = await fetch(`/api/v1/public/goals?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function createGoal(body) {
  const response = await fetch('/api/v1/public/goals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchGoal(goalId) {
  const response = await fetch(`/api/v1/public/goals/${encodeURIComponent(goalId)}`)
  return expectJson(response)
}

export async function checkInGoal(goalId, body) {
  const response = await fetch(`/api/v1/public/goals/${encodeURIComponent(goalId)}/check-in`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function explainGoal(goalId) {
  const response = await fetch(`/api/v1/public/goals/${encodeURIComponent(goalId)}/planner`, {
    method: 'POST',
  })
  return expectJson(response)
}
