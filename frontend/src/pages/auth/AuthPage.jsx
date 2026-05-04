import { useState, useCallback } from 'react'

import { useAuth } from '../../modules/auth'
import './auth.css'

export default function AuthPage({ mode = 'login', onAuthSuccess, onNavigateHome, onSwitchMode }) {
  const isRegister = mode === 'register'
  const { login, register, isLoading, error, setError } = useAuth()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [agreedTerms, setAgreedTerms] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault()
      setError('')

      let result = null

      if (isRegister) {
        if (!agreedTerms) {
          setError('Vui lòng đồng ý với điều khoản sử dụng.')
          return
        }
        result = await register(name, email, password, confirmPassword)
      } else {
        result = await login(email, password)
      }

      if (result) {
        onAuthSuccess?.(result)
      }
    },
    [isRegister, name, email, password, confirmPassword, agreedTerms, login, register, onAuthSuccess, setError],
  )

  function handleSwitchMode() {
    setIsTransitioning(true)
    setError('')
    setTimeout(() => {
      onSwitchMode?.(isRegister ? 'login' : 'register')
      setIsTransitioning(false)
    }, 180)
  }

  return (
    <section className="auth-page" aria-label={isRegister ? 'Đăng ký tài khoản' : 'Đăng nhập'}>
      {/* ─── Left: Hero ─── */}
      <div className="auth-hero">
        <div className="auth-hero-content">
          <div className="auth-hero-brand">
            <i aria-hidden="true" />
            <strong>Northstar Finance</strong>
          </div>
          <h1>
            Hiểu tài chính.{'\n'}
            Hành động thông minh hơn.
          </h1>
          <p>
            Nền tảng AI giúp bạn quản lý tài chính cá nhân, đặt mục tiêu, học kiến thức và phân tích thị trường — tất cả trong một hệ sinh thái an toàn.
          </p>
          <div className="auth-hero-features">
            <div className="auth-hero-feature">
              <span className="auth-hero-feature-icon" aria-hidden="true">
                <ShieldIcon />
              </span>
              <span>An toàn & minh bạch — AI giải thích, không phím hàng</span>
            </div>
            <div className="auth-hero-feature">
              <span className="auth-hero-feature-icon" aria-hidden="true">
                <ChartIcon />
              </span>
              <span>Dữ liệu thị trường real-time, phân tích BCTC tự động</span>
            </div>
            <div className="auth-hero-feature">
              <span className="auth-hero-feature-icon" aria-hidden="true">
                <TargetIcon />
              </span>
              <span>Goal planner & Financial Health theo dõi tiến độ cá nhân</span>
            </div>
            <div className="auth-hero-feature">
              <span className="auth-hero-feature-icon" aria-hidden="true">
                <BookIcon />
              </span>
              <span>Learning Hub — học tài chính theo trình độ, có AI tutor</span>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Right: Form ─── */}
      <div className="auth-form-panel">
        <div className={`auth-card${isTransitioning ? ' auth-card--transitioning' : ''}`}>
          <button type="button" className="auth-back" onClick={onNavigateHome} id="auth-back-btn">
            <ArrowLeftIcon />
            <span>Về trang chủ</span>
          </button>
          <div className="auth-card-header">
            <h2>{isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}</h2>
            <p>
              {isRegister
                ? 'Bắt đầu hành trình tài chính thông minh cùng Northstar.'
                : 'Chào mừng bạn quay lại Northstar Finance.'}
            </p>
          </div>

          {/* Social Login */}
          <div className="auth-social-row">
            <button type="button" className="auth-social-button" id="auth-google-btn">
              <GoogleIcon />
              Google
            </button>
            <button type="button" className="auth-social-button" id="auth-apple-btn">
              <AppleIcon />
              Apple
            </button>
          </div>

          <div className="auth-divider">
            <span>hoặc dùng email</span>
          </div>

          {/* Form */}
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {isRegister ? (
              <div className="auth-field">
                <label htmlFor="auth-name">Họ và tên</label>
                <input
                  id="auth-name"
                  type="text"
                  placeholder="Nguyễn Văn A"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  autoComplete="name"
                  required
                />
              </div>
            ) : null}

            <div className="auth-field">
              <label htmlFor="auth-email">Email</label>
              <input
                id="auth-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="auth-field">
              <label htmlFor="auth-password">Mật khẩu</label>
              <div className="auth-field-password">
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            {isRegister ? (
              <div className="auth-field">
                <label htmlFor="auth-confirm-password">Xác nhận mật khẩu</label>
                <div className="auth-field-password">
                  <input
                    id="auth-confirm-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    autoComplete="new-password"
                    required
                    minLength={6}
                  />
                </div>
              </div>
            ) : null}

            {isRegister ? (
              <div className="auth-terms">
                <input
                  id="auth-terms"
                  type="checkbox"
                  checked={agreedTerms}
                  onChange={(event) => setAgreedTerms(event.target.checked)}
                />
                <span>
                  Tôi đồng ý với{' '}
                  <a href="#terms" onClick={(e) => e.preventDefault()}>
                    Điều khoản sử dụng
                  </a>{' '}
                  và{' '}
                  <a href="#privacy" onClick={(e) => e.preventDefault()}>
                    Chính sách bảo mật
                  </a>
                </span>
              </div>
            ) : null}

            {error ? (
              <div className="auth-error" role="alert">
                <AlertCircleIcon />
                <span>{error}</span>
              </div>
            ) : null}

            <button
              type="submit"
              className={`auth-submit${isLoading ? ' auth-submit--loading' : ''}`}
              disabled={isLoading}
              id="auth-submit-btn"
            >
              {isLoading ? (
                <>
                  <span className="auth-spinner" />
                  Đang xử lý...
                </>
              ) : isRegister ? (
                'Tạo tài khoản'
              ) : (
                'Đăng nhập'
              )}
            </button>
          </form>

          <div className="auth-footer">
            {!isRegister ? (
              <button type="button" className="auth-forgot" id="auth-forgot-btn">
                Quên mật khẩu?
              </button>
            ) : null}
            <p className="auth-toggle-text">
              {isRegister ? 'Đã có tài khoản? ' : 'Chưa có tài khoản? '}
              <button type="button" className="auth-toggle-link" onClick={handleSwitchMode} id="auth-toggle-mode-btn">
                {isRegister ? 'Đăng nhập' : 'Đăng ký miễn phí'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ─── Inline SVG Icons ─── */

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  )
}

function AppleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C3.79 16.17 4.36 9.04 9.09 8.76c1.3.07 2.21.72 2.97.77.98-.2 1.92-.77 2.97-.7 1.25.1 2.2.58 2.82 1.49-2.59 1.54-1.97 4.93.4 5.87-.47 1.24-.68 1.84-1.2 2.94zM12.03 8.7c-.15-2.23 1.66-4.17 3.82-4.35.29 2.4-2.13 4.48-3.82 4.35z" />
    </svg>
  )
}

function EyeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeOffIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function AlertCircleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  )
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  )
}

function ChartIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function TargetIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
}

function BookIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}

function ArrowLeftIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  )
}
