function formatErrorMessage(payload, status) {
  const detail = payload?.detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === 'object') {
          const loc = Array.isArray(item.loc) ? item.loc.join('.') : ''
          return loc ? `${loc}: ${item.msg || ''}`.trim() : String(item.msg || '')
        }
        return String(item)
      })
      .filter(Boolean)
      .join('; ') || `Request failed: ${status}`
  }
  if (typeof detail === 'string' && detail) return detail
  if (typeof payload?.message === 'string' && payload.message) return payload.message
  return `Request failed: ${status}`
}

async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(formatErrorMessage(payload, response.status))
  }
  return payload
}

export async function fetchLearningHome(sessionId) {
  const response = await fetch(`/api/v1/public/learning/home?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function fetchLearningLesson(sessionId, lessonId) {
  const response = await fetch(
    `/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}?session_id=${encodeURIComponent(sessionId)}`,
  )
  return expectJson(response)
}

export async function submitLearningQuiz(sessionId, lessonId, answers) {
  const response = await fetch(`/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/quiz`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, answers }),
  })
  return expectJson(response)
}

export async function completeLearningLesson(sessionId, lessonId) {
  const response = await fetch(
    `/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/complete?session_id=${encodeURIComponent(sessionId)}`,
    { method: 'POST' },
  )
  return expectJson(response)
}

export async function fetchLearningContext(trigger) {
  const response = await fetch(`/api/v1/public/learning/context?trigger=${encodeURIComponent(trigger)}`)
  return expectJson(response)
}

export async function fetchLearningAssets(kind = 'videos') {
  const response = await fetch(`/api/v1/public/learning/assets?kind=${encodeURIComponent(kind)}`)
  return expectJson(response)
}

export async function fetchLearningCatalog(kind = 'video', { topic, tier, language, limit } = {}) {
  const params = new URLSearchParams({ kind })
  if (topic) params.set('topic', topic)
  if (tier) params.set('tier', tier)
  if (language) params.set('language', language)
  if (limit) params.set('limit', String(limit))
  const response = await fetch(`/api/v1/public/learning/catalog?${params.toString()}`)
  return expectJson(response)
}

export async function fetchLearningCatalogTopics() {
  const response = await fetch('/api/v1/public/learning/catalog/topics')
  return expectJson(response)
}
