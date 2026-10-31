export const SESSION_INVALID_EVENT = 'northstar:session-invalid'
export function clearStoredSession(storage = window.localStorage) {
  for (const key of ['public-beta.session_id','public-beta.user_profile','public-beta.view','pro_lab.access_token']) storage.removeItem(key)
}
export async function authenticatedFetch(url, options = {}, sessionId = window.localStorage.getItem('public-beta.session_id')) {
  const headers = new Headers(options.headers)
  if (sessionId) headers.set('Authorization', `Bearer ${sessionId}`)
  const response = await fetch(url, {...options, headers})
  if (response.status === 401 && sessionId) window.dispatchEvent(new CustomEvent(SESSION_INVALID_EVENT, {detail:{sessionId}}))
  return response
}
export async function verifySession(sessionId, {fetchImpl = fetch} = {}) {
  const response = await fetchImpl('/api/v1/public/auth/me', {headers:{Authorization:`Bearer ${sessionId}`}})
  if (!response.ok) throw Object.assign(new Error(response.status===401?'Phiên đã hết hiệu lực. Vui lòng đăng nhập lại.':'Chưa xác minh được phiên. Vui lòng thử lại.'),{status:response.status})
  const payload = await response.json()
  if (!payload?.profile?.account_id || payload.session_id !== sessionId) throw new Error('Phản hồi xác thực không hợp lệ.')
  return payload
}
