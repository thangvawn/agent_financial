async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

function adminHeaders(adminKey, role, hasJson = false) {
  return {
    ...(hasJson ? { 'Content-Type': 'application/json' } : {}),
    'X-Admin-Content-Ops-Key': adminKey,
    'X-Content-Ops-Role': role,
  }
}

export async function fetchContentOpsStatus(adminKey, role) {
  const response = await fetch('/admin/cms/status', {
    headers: adminHeaders(adminKey, role),
  })
  return expectJson(response)
}

export async function listContentOpsItems(adminKey, role, contentType = '') {
  const query = contentType ? `?content_type=${encodeURIComponent(contentType)}` : ''
  const response = await fetch(`/admin/cms/content${query}`, {
    headers: adminHeaders(adminKey, role),
  })
  return expectJson(response)
}

export async function fetchContentOpsItem(adminKey, role, contentId) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}`, {
    headers: adminHeaders(adminKey, role),
  })
  return expectJson(response)
}

export async function upsertContentOpsItem(adminKey, role, contentType, contentId, body) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentType)}/${encodeURIComponent(contentId)}`, {
    method: 'PUT',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function submitContentOpsReview(adminKey, role, contentId, body = {}) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}/submit-review`, {
    method: 'POST',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function approveContentOpsItem(adminKey, role, contentId, body = {}) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}/approve`, {
    method: 'POST',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function publishContentOpsItem(adminKey, role, contentId, body = {}) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}/publish`, {
    method: 'POST',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function archiveContentOpsItem(adminKey, role, contentId, body = {}) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}/archive`, {
    method: 'POST',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function rollbackContentOpsItem(adminKey, role, contentId, body) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}/rollback`, {
    method: 'POST',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function listContentOpsVersions(adminKey, role, contentId) {
  const response = await fetch(`/admin/cms/content/${encodeURIComponent(contentId)}/versions`, {
    headers: adminHeaders(adminKey, role),
  })
  return expectJson(response)
}

export async function fetchContentOpsReviewQueue(adminKey, role) {
  const response = await fetch('/admin/cms/review-queue', {
    headers: adminHeaders(adminKey, role),
  })
  return expectJson(response)
}

export async function fetchContentOpsAnalytics(adminKey, role, contentId) {
  const response = await fetch(`/admin/cms/analytics/content/${encodeURIComponent(contentId)}`, {
    headers: adminHeaders(adminKey, role),
  })
  return expectJson(response)
}

export async function generateContentOpsAiDraft(adminKey, role, body) {
  const response = await fetch('/admin/cms/ai/generate-draft', {
    method: 'POST',
    headers: adminHeaders(adminKey, role, true),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
