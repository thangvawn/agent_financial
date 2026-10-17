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

export async function fetchVideoAgentStatus(sessionId, lessonId, sourceUrl) {
  const params = new URLSearchParams()
  if (sessionId) params.set('session_id', sessionId)
  if (sourceUrl) params.set('source_url', sourceUrl)
  const response = await fetch(`/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/video-agent?${params.toString()}`)
  return expectJson(response)
}

export async function prepareVideoAgent(sessionId, lessonId, { sourceUrl, transcriptText, language = 'vi', forceRefresh = false } = {}) {
  const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''
  const response = await fetch(`/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/video-agent/prepare${query}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_url: sourceUrl || undefined,
      transcript_text: transcriptText || undefined,
      language,
      force_refresh: forceRefresh,
    }),
  })
  return expectJson(response)
}

export async function fetchVideoAgentCheckpoint(sessionId, lessonId, { sourceUrl, currentTimeSeconds = 0 } = {}) {
  const params = new URLSearchParams({ current_time_seconds: String(Math.max(0, currentTimeSeconds || 0)) })
  if (sessionId) params.set('session_id', sessionId)
  if (sourceUrl) params.set('source_url', sourceUrl)
  const response = await fetch(`/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/video-agent/checkpoint?${params.toString()}`)
  return expectJson(response)
}

export async function gradeVideoAgentCheckpoint(sessionId, lessonId, checkpointId, responseText) {
  const response = await fetch(`/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/video-agent/checkpoint/grade${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ checkpoint_id: checkpointId, response: responseText }),
  })
  return expectJson(response)
}

export async function askVideoAgent(sessionId, lessonId, { question, sourceUrl, currentTimeSeconds = 0, windowSeconds = 45 } = {}) {
  const response = await fetch(`/api/v1/public/learning/lessons/${encodeURIComponent(lessonId)}/video-agent/ask${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      source_url: sourceUrl || undefined,
      current_time_seconds: Math.max(0, currentTimeSeconds || 0),
      window_seconds: windowSeconds,
      language: 'vi',
    }),
  })
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

export async function fetchCheckpoint(sessionIdOrLessonOrOptions, lessonIdOrOptions, maybeDifficulty) {
  let sessionId, lessonId, difficulty
  if (typeof sessionIdOrLessonOrOptions === 'object' && sessionIdOrLessonOrOptions !== null) {
    lessonId = sessionIdOrLessonOrOptions.lesson_id || sessionIdOrLessonOrOptions.lessonId
    difficulty = sessionIdOrLessonOrOptions.difficulty
    sessionId = sessionIdOrLessonOrOptions.session_id || sessionIdOrLessonOrOptions.sessionId
  } else if (typeof lessonIdOrOptions === 'object' && lessonIdOrOptions !== null) {
    lessonId = sessionIdOrLessonOrOptions
    difficulty = lessonIdOrOptions.difficulty
    sessionId = lessonIdOrOptions.session_id || lessonIdOrOptions.sessionId
  } else if (maybeDifficulty !== undefined) {
    sessionId = sessionIdOrLessonOrOptions
    lessonId = lessonIdOrOptions
    difficulty = maybeDifficulty
  } else if (sessionIdOrLessonOrOptions && lessonIdOrOptions) {
    if (String(sessionIdOrLessonOrOptions).startsWith('lesson_')) {
      lessonId = sessionIdOrLessonOrOptions
      difficulty = lessonIdOrOptions
    } else {
      sessionId = sessionIdOrLessonOrOptions
      lessonId = lessonIdOrOptions
    }
  } else {
    lessonId = sessionIdOrLessonOrOptions
  }

  const params = new URLSearchParams()
  if (lessonId) params.set('lesson_id', lessonId)
  if (difficulty) params.set('difficulty', difficulty)
  if (sessionId) params.set('session_id', sessionId)

  const response = await fetch(`/api/v1/public/learning/checkpoint?${params.toString()}`)
  return expectJson(response)
}

export async function gradeCheckpoint(sessionIdOrPayload, checkpointId, responseText) {
  let sessionId, checkpoint_id, response
  if (typeof sessionIdOrPayload === 'object' && sessionIdOrPayload !== null) {
    checkpoint_id = sessionIdOrPayload.checkpoint_id || sessionIdOrPayload.checkpointId
    response = sessionIdOrPayload.response
    sessionId = sessionIdOrPayload.session_id || sessionIdOrPayload.sessionId
  } else if (responseText !== undefined) {
    sessionId = sessionIdOrPayload
    checkpoint_id = checkpointId
    response = responseText
  } else {
    checkpoint_id = sessionIdOrPayload
    response = checkpointId
  }

  const url = sessionId
    ? `/api/v1/public/learning/checkpoint/grade?session_id=${encodeURIComponent(sessionId)}`
    : '/api/v1/public/learning/checkpoint/grade'

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      schema_version: '1.0.0',
      checkpoint_id,
      response,
    }),
  })
  return expectJson(res)
}

export async function completeCheckpoint(sessionIdOrPayload, verifiedEventId, idempotencyKey, confirmationId) {
  let sessionId, verified_event_id, idempotency_key, confirmation_id
  if (typeof sessionIdOrPayload === 'object' && sessionIdOrPayload !== null) {
    verified_event_id = sessionIdOrPayload.verified_event_id || sessionIdOrPayload.verifiedEventId
    idempotency_key = sessionIdOrPayload.idempotency_key || sessionIdOrPayload.idempotencyKey
    confirmation_id = sessionIdOrPayload.confirmation_id || sessionIdOrPayload.confirmationId
    sessionId = sessionIdOrPayload.session_id || sessionIdOrPayload.sessionId
  } else if (idempotencyKey !== undefined) {
    sessionId = sessionIdOrPayload
    verified_event_id = verifiedEventId
    idempotency_key = idempotencyKey
    confirmation_id = confirmationId
  } else {
    verified_event_id = sessionIdOrPayload
    idempotency_key = verifiedEventId
  }

  const url = sessionId
    ? `/api/v1/public/learning/checkpoint/complete?session_id=${encodeURIComponent(sessionId)}`
    : '/api/v1/public/learning/checkpoint/complete'

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      schema_version: '1.0.0',
      verified_event_id,
      idempotency_key,
      confirmation_id: confirmation_id || `conf_${Date.now()}`,
    }),
  })
  return expectJson(res)
}
