import { useState, useCallback } from 'react'

const SESSION_KEY = 'public-beta.session_id'
const USER_KEY = 'public-beta.user_profile'

async function postJson(path, body) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload?.detail
    let message
    if (Array.isArray(detail)) {
      message = detail
        .map((item) => {
          if (item && typeof item === 'object') {
            const loc = Array.isArray(item.loc) ? item.loc.join('.') : ''
            return loc ? `${loc}: ${item.msg || ''}`.trim() : String(item.msg || '')
          }
          return String(item)
        })
        .filter(Boolean)
        .join('; ')
    } else if (typeof detail === 'string') {
      message = detail
    } else if (typeof payload?.message === 'string') {
      message = payload.message
    }
    throw new Error(message || `Request failed: ${response.status}`)
  }
  return payload
}

async function getJson(path) {
  const response = await fetch(path)
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = (typeof payload?.detail === 'string' && payload.detail) || `Request failed: ${response.status}`
    throw new Error(message)
  }
  return payload
}

function persistSession(sessionId, profile) {
  try {
    window.localStorage.setItem(SESSION_KEY, sessionId)
    window.localStorage.setItem(USER_KEY, JSON.stringify(profile))
  } catch {
    /* ignore quota errors */
  }
}

function clearSession() {
  try {
    window.localStorage.removeItem(SESSION_KEY)
    window.localStorage.removeItem(USER_KEY)
  } catch {
    /* ignore */
  }
}

/**
 * Auth hook that calls the backend /api/v1/public/auth endpoints.
 */
export function useAuth() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const login = useCallback(async (email, password) => {
    setError('')
    if (!email || !password) {
      setError('Vui lòng nhập email và mật khẩu.')
      return null
    }
    setIsLoading(true)
    try {
      const payload = await postJson('/api/v1/public/auth/login', { email, password })
      persistSession(payload.session_id, payload.profile)
      return { session_id: payload.session_id, profile: payload.profile }
    } catch (err) {
      setError(err.message || 'Đăng nhập thất bại.')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loginWithGoogle = useCallback(async (credential) => {
    setError('')
    if (!credential) {
      setError('Không nhận được thông tin đăng nhập từ Google.')
      return null
    }
    setIsLoading(true)
    try {
      const payload = await postJson('/api/v1/public/auth/google', { credential })
      persistSession(payload.session_id, payload.profile)
      return { session_id: payload.session_id, profile: payload.profile }
    } catch (err) {
      setError(err.message || 'Đăng nhập Google thất bại.')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  const register = useCallback(async (name, email, password, confirmPassword) => {
    setError('')
    if (!name || !email || !password) {
      setError('Vui lòng điền đầy đủ thông tin.')
      return null
    }
    if (password.length < 8) {
      setError('Mật khẩu phải có ít nhất 8 ký tự.')
      return null
    }
    if (password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp.')
      return null
    }
    setIsLoading(true)
    try {
      const payload = await postJson('/api/v1/public/auth/register', { name, email, password })
      persistSession(payload.session_id, payload.profile)
      return { session_id: payload.session_id, profile: payload.profile }
    } catch (err) {
      setError(err.message || 'Đăng ký thất bại.')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    const sessionId = (typeof window !== 'undefined' && window.localStorage.getItem(SESSION_KEY)) || ''
    clearSession()
    if (!sessionId) return
    try {
      await postJson('/api/v1/public/auth/logout', { session_id: sessionId })
    } catch {
      /* best-effort; client state is already cleared */
    }
  }, [])

  const getStoredSession = useCallback(() => {
    try {
      return window.localStorage.getItem(SESSION_KEY) || ''
    } catch {
      return ''
    }
  }, [])

  const getStoredProfile = useCallback(() => {
    try {
      return JSON.parse(window.localStorage.getItem(USER_KEY) || 'null')
    } catch {
      return null
    }
  }, [])

  const verifyStoredSession = useCallback(async () => {
    const sessionId = (typeof window !== 'undefined' && window.localStorage.getItem(SESSION_KEY)) || ''
    if (!sessionId) return null
    try {
      const payload = await getJson(`/api/v1/public/auth/me?session_id=${encodeURIComponent(sessionId)}`)
      persistSession(payload.session_id, payload.profile)
      return { session_id: payload.session_id, profile: payload.profile }
    } catch {
      clearSession()
      return null
    }
  }, [])

  return {
    login,
    loginWithGoogle,
    register,
    logout,
    getStoredSession,
    getStoredProfile,
    verifyStoredSession,
    isLoading,
    error,
    setError,
  }
}
