import { useState, useCallback } from 'react'

const SESSION_KEY = 'public-beta.session_id'
const USER_KEY = 'public-beta.user_profile'

function generateSessionId() {
  return 'sess_' + crypto.randomUUID()
}

/**
 * Auth hook — mock mode.
 * When a real backend is available, swap the mock logic for API calls.
 */
export function useAuth() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const login = useCallback(async (email, password) => {
    setError('')
    setIsLoading(true)

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 800))

    if (!email || !password) {
      setIsLoading(false)
      setError('Vui lòng nhập email và mật khẩu.')
      return null
    }

    if (password.length < 6) {
      setIsLoading(false)
      setError('Mật khẩu phải có ít nhất 6 ký tự.')
      return null
    }

    // Mock: accept any valid-looking email + password
    const sessionId = generateSessionId()
    const profile = { email, name: email.split('@')[0] }

    window.localStorage.setItem(SESSION_KEY, sessionId)
    window.localStorage.setItem(USER_KEY, JSON.stringify(profile))

    setIsLoading(false)
    return { session_id: sessionId, profile }
  }, [])

  const register = useCallback(async (name, email, password, confirmPassword) => {
    setError('')
    setIsLoading(true)

    await new Promise((resolve) => setTimeout(resolve, 1000))

    if (!name || !email || !password) {
      setIsLoading(false)
      setError('Vui lòng điền đầy đủ thông tin.')
      return null
    }

    if (password.length < 6) {
      setIsLoading(false)
      setError('Mật khẩu phải có ít nhất 6 ký tự.')
      return null
    }

    if (password !== confirmPassword) {
      setIsLoading(false)
      setError('Mật khẩu xác nhận không khớp.')
      return null
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailPattern.test(email)) {
      setIsLoading(false)
      setError('Email không hợp lệ.')
      return null
    }

    const sessionId = generateSessionId()
    const profile = { email, name }

    window.localStorage.setItem(SESSION_KEY, sessionId)
    window.localStorage.setItem(USER_KEY, JSON.stringify(profile))

    setIsLoading(false)
    return { session_id: sessionId, profile }
  }, [])

  const logout = useCallback(() => {
    window.localStorage.removeItem(SESSION_KEY)
    window.localStorage.removeItem(USER_KEY)
  }, [])

  const getStoredSession = useCallback(() => {
    return window.localStorage.getItem(SESSION_KEY) || ''
  }, [])

  const getStoredProfile = useCallback(() => {
    try {
      return JSON.parse(window.localStorage.getItem(USER_KEY) || 'null')
    } catch {
      return null
    }
  }, [])

  return { login, register, logout, getStoredSession, getStoredProfile, isLoading, error, setError }
}
