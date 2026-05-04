async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

function headers(adminKey) {
  return {
    'Content-Type': 'application/json',
    'X-Admin-Trust-Safety-Key': adminKey || '',
  }
}

export async function fetchTrustSafetyStatus(adminKey) {
  const response = await fetch('/admin/trust-safety/status', {
    headers: { 'X-Admin-Trust-Safety-Key': adminKey || '' },
  })
  return expectJson(response)
}

export async function fetchTrustSafetyAudit(adminKey, filters = {}) {
  const query = new URLSearchParams()
  if (filters.surface) query.set('surface', filters.surface)
  if (filters.riskClass) query.set('risk_class', filters.riskClass)
  if (filters.severity) query.set('severity', filters.severity)
  if (filters.search) query.set('search', filters.search)
  const response = await fetch(`/admin/trust-safety/audit${query.toString() ? `?${query}` : ''}`, {
    headers: { 'X-Admin-Trust-Safety-Key': adminKey || '' },
  })
  return expectJson(response)
}

export async function fetchTrustSafetyIncidents(adminKey, filters = {}) {
  const query = new URLSearchParams()
  if (filters.surface) query.set('surface', filters.surface)
  if (filters.status) query.set('status', filters.status)
  if (filters.severity) query.set('severity', filters.severity)
  if (filters.search) query.set('search', filters.search)
  const response = await fetch(`/admin/trust-safety/incidents${query.toString() ? `?${query}` : ''}`, {
    headers: { 'X-Admin-Trust-Safety-Key': adminKey || '' },
  })
  return expectJson(response)
}

export async function openTrustSafetyIncident(adminKey, body) {
  const response = await fetch('/admin/trust-safety/incidents/open', {
    method: 'POST',
    headers: headers(adminKey),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function actOnTrustSafetyIncident(adminKey, incidentId, body) {
  const response = await fetch(`/admin/trust-safety/incidents/${encodeURIComponent(incidentId)}/action`, {
    method: 'POST',
    headers: headers(adminKey),
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
