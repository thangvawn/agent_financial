async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function respondWithAssistant(body) {
  const response = await fetch('/api/v1/public/ai-assistant/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function synthesizeAssistantVoice(body) {
  const response = await fetch('/api/v1/public/ai-assistant/voice/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
