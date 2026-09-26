/**
 * Simulation & Strategy Research Agent API Client (Module 6 - G8).
 * Handles 2-Phase Action Execution (Propose -> Confirm -> Execute) and Tool Invocations.
 */

export interface ReproducibilityManifest {
  schema_version?: string
  strategy_id: string
  strategy_version?: string
  dataset_source: string
  dataset_version: string
  data_start: string
  data_end: string
  parameters?: Record<string, any>
  commission_pct?: number
  slippage_pct?: number
  benchmark?: string
  random_seed?: number | null
  engine_version?: string
  execution_timestamp?: string
  metrics_calculation_version?: string
  warnings?: string[]
  data_gaps?: string[]
}

export interface ActionProposal {
  schema_version: string
  proposal_id: string
  run_id: string
  account_id: string
  operation: string
  manifest: ReproducibilityManifest
  estimated_cost: number
  risk_class: string
  requires_confirmation: boolean
  policy_version: string
  created_at: string
  expires_at: string
}

export interface ActionReceipt {
  schema_version: string
  receipt_id: string
  proposal_id: string
  account_id: string
  status: string
  risk_class: string
  executed_at: string
  run_artifact_id?: string
  error_code?: string | null
}

export interface ExecuteRunPayload {
  proposal_id: string
  confirmation_token: string
  idempotency_key?: string
}

const BASE_URL = '/api/v1/public/simulation/agent'

function getAuthHeaders(token?: string, idempotencyKey?: string): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const authToken = token || localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey
  }
  return headers
}

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const errorMsg = data?.detail?.message || data?.detail || data?.message || `Request failed with status ${res.status}`
    const error = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
    ;(error as any).status = res.status
    ;(error as any).data = data
    throw error
  }
  return data as T
}

export async function listTools(options?: { token?: string }): Promise<{ tools: any[] }> {
  const res = await fetch(`${BASE_URL}/tools`, {
    method: 'GET',
    headers: getAuthHeaders(options?.token),
  })
  return handleResponse(res)
}

export async function invokeTool(
  toolId: string,
  input: Record<string, any>,
  options?: { token?: string; idempotencyKey?: string }
): Promise<{ tool_id: string; output: any; latency_ms: number }> {
  const res = await fetch(`${BASE_URL}/tools/${encodeURIComponent(toolId)}:invoke`, {
    method: 'POST',
    headers: getAuthHeaders(options?.token, options?.idempotencyKey),
    body: JSON.stringify({ input }),
  })
  return handleResponse(res)
}

export async function createProposal(
  manifest: ReproducibilityManifest,
  estimatedCost = 0.02,
  options?: { token?: string }
): Promise<ActionProposal> {
  const res = await fetch(`${BASE_URL}/proposals`, {
    method: 'POST',
    headers: getAuthHeaders(options?.token),
    body: JSON.stringify({ manifest, estimated_cost: estimatedCost }),
  })
  return handleResponse<ActionProposal>(res)
}

export async function getProposal(
  proposalId: string,
  options?: { token?: string }
): Promise<ActionProposal> {
  const res = await fetch(`${BASE_URL}/proposals/${encodeURIComponent(proposalId)}`, {
    method: 'GET',
    headers: getAuthHeaders(options?.token),
  })
  return handleResponse<ActionProposal>(res)
}

export async function executeRun(
  payload: ExecuteRunPayload,
  options?: { token?: string }
): Promise<ActionReceipt> {
  const res = await fetch(`${BASE_URL}/execute`, {
    method: 'POST',
    headers: getAuthHeaders(options?.token, payload.idempotency_key),
    body: JSON.stringify(payload),
  })
  return handleResponse<ActionReceipt>(res)
}

export async function createAgentRun(
  payload: {
    skill_id: string
    run_id?: string
    blueprint_id?: string
    manifest?: ReproducibilityManifest
    compare_run_ids?: string[]
  },
  options?: { token?: string }
): Promise<{
  run_id: string
  skill_id: string
  status: string
  narrative: string
  citations: string[]
  methodology_warnings: string[]
}> {
  const res = await fetch(`${BASE_URL}/runs`, {
    method: 'POST',
    headers: getAuthHeaders(options?.token),
    body: JSON.stringify(payload),
  })
  return handleResponse(res)
}

export async function getRun(
  runId: string,
  options?: { token?: string }
): Promise<any> {
  const res = await fetch(`${BASE_URL}/runs/${encodeURIComponent(runId)}`, {
    method: 'GET',
    headers: getAuthHeaders(options?.token),
  })
  return handleResponse(res)
}

