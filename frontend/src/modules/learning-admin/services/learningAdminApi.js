async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(message)
  }
  return payload
}

function adminHeaders(adminKey) {
  return {
    'Content-Type': 'application/json',
    'X-Admin-Learning-Cms-Key': adminKey,
  }
}

export async function fetchLearningCmsStatus(adminKey) {
  const response = await fetch('/admin/learning-cms/status', {
    headers: { 'X-Admin-Learning-Cms-Key': adminKey },
  })
  return expectJson(response)
}

export async function listLearningCmsDocuments(docType, adminKey) {
  const response = await fetch(`/admin/learning-cms/${encodeURIComponent(docType)}`, {
    headers: { 'X-Admin-Learning-Cms-Key': adminKey },
  })
  return expectJson(response)
}

export async function fetchLearningCmsDocument(docType, docId, adminKey) {
  const response = await fetch(`/admin/learning-cms/${encodeURIComponent(docType)}/${encodeURIComponent(docId)}`, {
    headers: { 'X-Admin-Learning-Cms-Key': adminKey },
  })
  return expectJson(response)
}

export async function upsertLearningCmsDocument(docType, docId, body, adminKey) {
  const response = await fetch(`/admin/learning-cms/${encodeURIComponent(docType)}/${encodeURIComponent(docId)}`, {
    method: 'PUT',
    headers: adminHeaders(adminKey),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
