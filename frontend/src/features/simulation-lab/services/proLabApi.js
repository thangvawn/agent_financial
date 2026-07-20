async function expectJson(response) {
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return payload
}

export async function fetchProLabTeaser(sessionId) {
  const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''
  const response = await fetch(`/api/v1/public/pro-lab/teaser${query}`)
  return expectJson(response)
}

export async function issueProLabAccessToken(sessionId) {
  const response = await fetch('/api/v1/public/pro-lab/access-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  })
  return expectJson(response)
}

export async function fetchProLabWorkspace(userId, accessToken) {
  const response = await fetch(`/api/v1/pro/pro-lab/workspace?user_id=${encodeURIComponent(userId)}`, {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function fetchProLabCatalog(accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/catalog', {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function fetchProLabWorkspaceState(userId, accessToken) {
  const response = await fetch(`/api/v1/pro/pro-lab/workspace-state?user_id=${encodeURIComponent(userId)}`, {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function saveProLabWorkspaceState(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/workspace-state', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchProLabSessions(userId, accessToken) {
  const response = await fetch(`/api/v1/pro/pro-lab/sessions?user_id=${encodeURIComponent(userId)}`, {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function runProLabCommand(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/runs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function fetchProLabRun(userId, runId, accessToken) {
  const params = new URLSearchParams({ user_id: userId })
  const response = await fetch(`/api/v1/pro/pro-lab/runs/${encodeURIComponent(runId)}?${params.toString()}`, {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function revokeProLabSession(userId, tokenId, accessToken) {
  const params = new URLSearchParams({ user_id: userId })
  const response = await fetch(
    `/api/v1/pro/pro-lab/sessions/${encodeURIComponent(tokenId)}/revoke?${params.toString()}`,
    {
      method: 'POST',
      headers: { 'X-Access-Token': accessToken || '' },
    },
  )
  return expectJson(response)
}

export async function createProLabBlueprint(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/blueprints', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function updateProLabBlueprint(blueprintId, body, accessToken) {
  const response = await fetch(`/api/v1/pro/pro-lab/blueprints/${encodeURIComponent(blueprintId)}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function archiveProLabBlueprint(blueprintId, userId, accessToken) {
  const response = await fetch(
    `/api/v1/pro/pro-lab/blueprints/${encodeURIComponent(blueprintId)}/archive?user_id=${encodeURIComponent(userId)}`,
    {
      method: 'POST',
      headers: { 'X-Access-Token': accessToken || '' },
    },
  )
  return expectJson(response)
}

export async function compareProLabBlueprints(userId, leftId, rightId, accessToken) {
  const params = new URLSearchParams({
    user_id: userId,
    left_id: leftId,
    right_id: rightId,
  })
  const response = await fetch(`/api/v1/pro/pro-lab/blueprints/compare?${params.toString()}`, {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function runProLabScenario(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/scenario-lab/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function runProLabBacktest(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/backtest-lab/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function exportProLabReport(userId, experimentId, accessToken) {
  const params = new URLSearchParams({
    user_id: userId,
  })
  const response = await fetch(
    `/api/v1/pro/pro-lab/experiments/${encodeURIComponent(experimentId)}/report?${params.toString()}`,
    {
      headers: { 'X-Access-Token': accessToken || '' },
    },
  )
  return expectJson(response)
}

export async function aiHealth(accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/ai/health', {
    headers: { 'X-Access-Token': accessToken || '' },
  })
  return expectJson(response)
}

export async function aiStrategyCopilot(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/ai/strategy-copilot', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function aiSwarmCommittee(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/ai/swarm-committee', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}

export async function aiBacktestCritique(body, accessToken) {
  const response = await fetch('/api/v1/pro/pro-lab/ai/backtest-critique', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Access-Token': accessToken || '',
    },
    body: JSON.stringify(body),
  })
  return expectJson(response)
}
