async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(message)
  }
  return payload
}

export async function startOnboarding() {
  const response = await fetch('/api/v1/public/onboarding/start', { method: 'POST' })
  return expectJson(response)
}

export async function submitOnboardingAnswers(sessionId, answersMap) {
  const answers = Object.entries(answersMap).map(([question_key, answer_value]) => ({
    question_key,
    answer_value,
  }))
  const response = await fetch('/api/v1/public/onboarding/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, answers }),
  })
  return expectJson(response)
}

export async function completeOnboarding(sessionId) {
  const response = await fetch('/api/v1/public/onboarding/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, answers: [] }),
  })
  return expectJson(response)
}

export async function fetchPersonalizedHome(sessionId) {
  const response = await fetch(`/api/v1/public/home/${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}
