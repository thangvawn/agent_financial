async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchCommunityHome(sessionId) {
  const response = await fetch(`/api/v1/public/community/home?session_id=${encodeURIComponent(sessionId)}`)
  return expectJson(response)
}

export async function joinCommunitySpace(sessionId, spaceId) {
  const response = await fetch('/api/v1/public/community/spaces/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, space_id: spaceId }),
  })
  return expectJson(response)
}

export async function fetchCommunityPosts(spaceId) {
  const response = await fetch(`/api/v1/public/community/spaces/${encodeURIComponent(spaceId)}/posts`)
  return expectJson(response)
}

export async function createCommunityPost(body) {
  const response = await fetch('/api/v1/public/community/spaces/posts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function createCommunityComment(body) {
  const response = await fetch('/api/v1/public/community/spaces/comments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchCommunityModerationQueue(moderatorKey, filters = {}) {
  const params = new URLSearchParams()
  if (filters.space_id) params.set('space_id', filters.space_id)
  if (filters.risk_label) params.set('risk_label', filters.risk_label)
  if (filters.search) params.set('search', filters.search)
  const query = params.toString()
  const response = await fetch(`/api/v1/public/community/moderation/queue${query ? `?${query}` : ''}`, {
    headers: { 'X-Community-Moderator-Key': moderatorKey || '' },
  })
  return expectJson(response)
}

export async function reviewCommunityModeration(body, moderatorKey) {
  const response = await fetch('/api/v1/public/community/moderation/review', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Community-Moderator-Key': moderatorKey || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function updateCommunityNotificationState(notificationId, action) {
  const response = await fetch(`/api/v1/public/community/notifications/${encodeURIComponent(notificationId)}/state`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
  return expectJson(response)
}
