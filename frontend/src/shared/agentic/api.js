// @ts-check

/**
 * Fetch wrapper for Agentic Core API
 * Gracefully degrades if endpoint returns 404.
 */

const BASE_URL = '/api/v1/public/agentic';

async function fetchJson(url, options = {}) {
  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  
  if (!res.ok) {
    if (res.status === 404) {
      return null;
    }
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed with status ${res.status}`);
  }
  
  return res.json();
}

export const agenticApi = {
  createRun: (payload) => fetchJson('/runs', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  
  getRun: (runId) => fetchJson(`/runs/${runId}`),
  
  cancelRun: (runId) => fetchJson(`/runs/${runId}:cancel`, { method: 'POST' }),
  
  getArtifact: (artifactId) => fetchJson(`/artifacts/${artifactId}`),
  
  confirmAction: (proposalId) => fetchJson(`/action-proposals/${proposalId}:confirm`, { method: 'POST' }),
  
  rejectAction: (proposalId) => fetchJson(`/action-proposals/${proposalId}:reject`, { method: 'POST' }),
};
