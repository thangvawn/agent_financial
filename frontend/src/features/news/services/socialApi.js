import { authenticatedFetch } from '../../auth/services/sessionClient'

const BASE = '/api/v1/public/news/social'

export async function socialRequest(path, sessionId, { method = 'GET', body, signal } = {}) {
  const response = await authenticatedFetch(`${BASE}${path}`, {
    method, signal,
    ...(body ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
  }, sessionId)
  const result = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = result?.detail
    const message = typeof detail === 'string' ? detail : response.status === 422
      ? 'Kiểm tra lại đường dẫn hoặc nội dung nhập vào.' : 'Chưa kết nối được Social. Vui lòng thử lại.'
    throw Object.assign(new Error(message), { status: response.status })
  }
  return result
}

export function fetchSocialFeed(sessionId, filters, { cursor, signal } = {}) {
  const params = new URLSearchParams({ ...filters, limit: '20' })
  if (cursor) params.set('cursor', cursor)
  return socialRequest(`/feed?${params}`, sessionId, { signal })
}

export function safeSocialUrl(url) {
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password) return null
    return ['www.youtube.com', 'www.reddit.com'].includes(parsed.hostname) ? parsed.href : null
  } catch { return null }
}
