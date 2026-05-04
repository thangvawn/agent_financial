async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function bootstrapProLabAdminToken(adminKey) {
  const response = await fetch('/admin/pro-lab/access/bootstrap', {
    method: 'POST',
    headers: { 'X-Admin-Trading-Lab-Key': adminKey || '' },
  })
  return expectJson(response)
}

export async function fetchProLabAdminExperiments(accessToken) {
  const response = await fetch('/admin/pro-lab/experiments', {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function fetchProLabAdminRuns(accessToken) {
  const response = await fetch('/admin/pro-lab/runs', {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function reviewProLabExperiment(experimentId, body, accessToken) {
  const response = await fetch(`/admin/pro-lab/experiments/${encodeURIComponent(experimentId)}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchProLabAuditLogs(accessToken) {
  const response = await fetch('/admin/pro-lab/audit', {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}
