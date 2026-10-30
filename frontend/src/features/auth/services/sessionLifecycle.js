export async function logoutSession({ storage = window.localStorage, fetchImpl = fetch } = {}) {
  const session = storage.getItem('public-beta.session_id')
  try {
    if (session) {
      const response = await fetchImpl('/api/v1/public/auth/logout', {
        method: 'POST', headers: { Authorization: `Bearer ${session}` },
      })
      if (!response.ok && response.status !== 401) throw new Error('Không thu hồi được phiên trên máy chủ. Vui lòng thử đăng xuất lại.')
    }
  } catch (error) {
    // Retain the credential so the user can retry revocation rather than lose it.
    throw new Error(error.message || 'Không kết nối được máy chủ để đăng xuất.')
  }
  for (const key of ['public-beta.session_id', 'public-beta.user_profile', 'public-beta.view', 'pro_lab.access_token']) storage.removeItem(key)
}
