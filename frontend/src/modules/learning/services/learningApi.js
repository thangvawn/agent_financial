async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(message)
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

export async function askLearningTutor(sessionId, lessonId, question, knowledgeLevel = 'beginner') {
  const response = await fetch('/api/v1/public/learning/tutor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      lesson_id: lessonId,
      question,
      knowledge_level: knowledgeLevel,
    }),
  })
  return expectJson(response)
}

export async function fetchLearningCoach(sessionId, trigger = 'continue_path') {
  const response = await fetch('/api/v1/public/learning/coach', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, trigger }),
  })
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
