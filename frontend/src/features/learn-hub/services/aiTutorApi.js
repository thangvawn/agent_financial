const SESSION_KEY = 'public-beta.session_id'

function getSessionId() {
  try {
    return localStorage.getItem(SESSION_KEY) || ''
  } catch {
    return ''
  }
}

function getHeaders(sessionId) {
  const token = sessionId || getSessionId()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const msg = payload?.detail || payload?.message || `Lỗi yêu cầu: ${response.status}`
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return payload
}

export async function createTutorConversation({ sessionId, surface = 'learn', contextId }) {
  const idemp = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
  const res = await fetch('/api/v1/public/ai-tutor/conversations', {
    method: 'POST',
    headers: getHeaders(sessionId),
    body: JSON.stringify({
      surface,
      context_id: contextId || null,
      idempotency_key: idemp,
    }),
  })
  return expectJson(res)
}

export async function getTutorConversation({ sessionId, conversationId }) {
  const res = await fetch(`/api/v1/public/ai-tutor/conversations/${encodeURIComponent(conversationId)}`, {
    headers: getHeaders(sessionId),
  })
  return expectJson(res)
}

export async function sendTutorMessage({
  sessionId,
  conversationId,
  content,
  surface = 'learn',
  currentSurfaceId,
  knowledgeLevel = 'beginner',
  videoTimeSeconds,
}) {
  const idemp = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
  const res = await fetch(`/api/v1/public/ai-tutor/conversations/${encodeURIComponent(conversationId)}/messages`, {
    method: 'POST',
    headers: getHeaders(sessionId),
    body: JSON.stringify({
      content,
      surface,
      current_surface_id: currentSurfaceId || null,
      knowledge_level: knowledgeLevel,
      locale: 'vi-VN',
      ...(Number.isFinite(videoTimeSeconds) ? { video_time_seconds: videoTimeSeconds } : {}),
      idempotency_key: idemp,
    }),
  })
  return expectJson(res)
}

export async function submitTutorFeedback({ sessionId, messageId, conversationId, rating, comment }) {
  const idemp = `fb_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`
  const res = await fetch(`/api/v1/public/ai-tutor/messages/${encodeURIComponent(messageId)}/feedback`, {
    method: 'POST',
    headers: getHeaders(sessionId),
    body: JSON.stringify({
      conversation_id: conversationId || null,
      rating,
      comment: comment || null,
      idempotency_key: idemp,
    }),
  })
  return expectJson(res)
}
