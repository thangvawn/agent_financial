import { useState, useCallback, useEffect, useRef } from 'react'

import { useAuth } from '../../modules/auth'
import './auth.css'

const GOOGLE_CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ||
  '483150503670-hd2qvbcvaq0qqre21qn94mgq21o9559k.apps.googleusercontent.com'

let googleIdentityScriptPromise = null

function loadGoogleIdentityScript() {
  if (typeof window === 'undefined') return Promise.reject(new Error('Browser unavailable'))
  if (window.google?.accounts?.id) return Promise.resolve()
  if (!googleIdentityScriptPromise) {
    googleIdentityScriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.defer = true
      script.onload = resolve
      script.onerror = () => reject(new Error('Không tải được Google Identity Services.'))
      document.head.appendChild(script)
    })
  }
  return googleIdentityScriptPromise
}

export default function AuthPage({ mode = 'login', onAuthSuccess, onNavigateHome, onSwitchMode }) {
  const isRegister = mode === 'register'
  const { login, loginWithGoogle, register, isLoading, error, setError } = useAuth()
  const googleButtonRef = useRef(null)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [agreedTerms, setAgreedTerms] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)

  useEffect(() => {
    let cancelled = false
    if (!GOOGLE_CLIENT_ID || !googleButtonRef.current) return undefined

    loadGoogleIdentityScript()
      .then(() => {
        if (cancelled || !window.google?.accounts?.id || !googleButtonRef.current) return
        googleButtonRef.current.innerHTML = ''
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: async (response) => {
            const result = await loginWithGoogle(response?.credential || '')
            if (result) onAuthSuccess?.(result)
          },
        })
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          shape: 'rectangular',
          text: isRegister ? 'signup_with' : 'signin_with',
          logo_alignment: 'left',
          width: googleButtonRef.current.getBoundingClientRect().width || 448,
        })
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Không tải được đăng nhập Google.')
      })

    return () => {
      cancelled = true
    }
  }, [isRegister, loginWithGoogle, onAuthSuccess, setError])

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
    <section 
      className="relative min-h-screen w-full grid grid-cols-1 lg:grid-cols-2 bg-[#060913] text-zinc-100 overflow-hidden font-sans dark" 
      aria-label={isRegister ? 'Đăng ký tài khoản' : 'Đăng nhập tài khoản'}
      data-theme="dark"
    >
      {/* Ambient background glows for whole page */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -top-[10%] -left-[10%] w-[60%] h-[50%] rounded-full bg-gradient-to-br from-teal-500/10 to-indigo-500/10 blur-[100px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[50%] rounded-full bg-gradient-to-br from-indigo-500/10 to-emerald-500/10 blur-[120px]" />
      </div>

      {/* ─── Left: Hero ─── */}
      <div className="hidden lg:flex flex-col justify-between p-16 bg-zinc-950/40 border-r border-zinc-900/50 relative overflow-hidden">
        {/* Glow backdrop inside Left Hero */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
          <div className="absolute top-[20%] -left-[20%] w-[90%] h-[50%] rounded-full bg-teal-500/5 blur-[80px] animate-pulse duration-[8s]" />
          <div className="absolute bottom-[10%] -right-[20%] w-[90%] h-[50%] rounded-full bg-indigo-500/5 blur-[90px] animate-pulse duration-[12s]" />
        </div>

        {/* Header/Brand */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-400 to-indigo-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
            <span className="text-white text-base font-extrabold tracking-tight">N</span>
          </div>
          <span className="text-base font-semibold tracking-tight text-white">
            Northstar <span className="text-teal-400 font-normal">Finance</span>
          </span>
        </div>

        {/* Headline & Features */}
        <div className="relative z-10 my-auto py-12 space-y-8 max-w-md">
          <div className="space-y-4">
            <h1 className="text-3xl xl:text-4xl font-bold tracking-tight text-white leading-tight">
              Hiểu tài chính.<br />
              <span className="bg-gradient-to-r from-teal-300 via-teal-400 to-emerald-400 bg-clip-text text-transparent">
                Hành động thông minh.
              </span>
            </h1>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Tạo tài khoản để lưu tiến độ học tài chính, theo dõi mục tiêu, đọc dữ liệu thị trường và tiếp tục hành trình phân tích của bạn.
            </p>
          </div>

          <div className="space-y-3.5">
            {[
              { icon: <ShieldIcon className="w-4 h-4 text-teal-400" />, text: "An toàn & minh bạch — AI giải thích, không phím hàng" },
              { icon: <ChartIcon className="w-4 h-4 text-teal-400" />, text: "Dữ liệu thị trường real-time, phân tích BCTC tự động" },
              { icon: <TargetIcon className="w-4 h-4 text-teal-400" />, text: "Goal planner & Financial Health theo dõi tiến độ" },
              { icon: <BookIcon className="w-4 h-4 text-teal-400" />, text: "Learning Hub — học tài chính có AI tutor" }
            ].map((item, idx) => (
              <div 
                key={idx} 
                className="flex items-start gap-3.5 p-3.5 rounded-xl bg-zinc-900/20 border border-zinc-900 hover:border-teal-500/20 backdrop-blur-sm hover:bg-zinc-900/30 transition-all duration-300 group"
              >
                <div className="flex-shrink-0 w-7.5 h-7.5 rounded-lg bg-zinc-950 flex items-center justify-center border border-zinc-900 group-hover:bg-teal-500/10 group-hover:border-teal-500/25 transition-all duration-300">
                  {item.icon}
                </div>
                <p className="text-xs font-medium text-zinc-400 pt-0.5 group-hover:text-zinc-300 transition-colors">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 text-[11px] text-zinc-500 flex justify-between items-center w-full">
          <span>© 2026 Northstar Finance Lab</span>
          <span className="flex items-center gap-1.5 text-teal-500/80 hover:text-teal-400 transition-colors cursor-pointer">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Active
          </span>
        </div>
      </div>

      {/* ─── Right: Form ─── */}
      <div className="flex flex-col justify-center items-center p-8 sm:p-12 md:p-16 relative bg-[#060913]">
        <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
          <div className="absolute top-[10%] right-[10%] w-[50%] h-[40%] rounded-full bg-gradient-to-br from-teal-500/5 to-transparent blur-[120px]" />
        </div>

        {/* Clean, Full-Width Centered Container */}
        <div className={`relative z-10 w-full max-w-md transition-all duration-200 ${
          isTransitioning ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
        }`}>
          {/* Back button */}
          <button 
            type="button" 
            onClick={onNavigateHome} 
            id="auth-back-btn"
            className="group mb-8 inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold !text-zinc-400 hover:!text-zinc-200 !bg-zinc-950/60 hover:!bg-zinc-950 !border-zinc-900 hover:!border-zinc-800 rounded-lg transition-all duration-200 cursor-pointer shadow-sm !h-auto !min-h-0"
          >
            <ArrowLeftIcon className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            <span>Về trang chủ</span>
          </button>

          {/* Form Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold tracking-tight !text-white">
              {isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}
            </h2>
            <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
              {isRegister
                ? 'Đăng ký tài khoản Northstar Finance để cá nhân hóa trải nghiệm học và phân tích.'
                : 'Đăng nhập để mở workspace tài chính cá nhân của bạn.'}
            </p>
          </div>

          {/* Google SSO Slot */}
          <div className="mb-6 flex justify-center w-full">
            <div 
              className="google-btn-container w-full h-[40px] rounded-lg overflow-hidden border border-zinc-800 hover:border-zinc-700 bg-white transition-colors" 
              ref={googleButtonRef} 
              aria-label="Đăng nhập bằng Google" 
            />
          </div>

          {/* Divider */}
          <div className="relative my-6" aria-hidden="true">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800/80"></div>
            </div>
            <div className="relative flex justify-center text-xs text-zinc-500 uppercase tracking-wider">
              <span className="px-3 bg-[#0d1323] text-zinc-500 rounded-full border border-zinc-800/50 py-0.5 font-semibold text-[10px]">
                Northstar Account
              </span>
            </div>
          </div>

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit} noValidate>
            {isRegister ? (
              <div className="space-y-1.5">
                <label htmlFor="auth-name" className="text-[10px] font-semibold !text-zinc-400 uppercase tracking-wider">
                  Họ và tên
                </label>
                <input
                  id="auth-name"
                  type="text"
                  placeholder="Nguyễn Văn A"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  autoComplete="name"
                  required
                  className="w-full px-3.5 py-2.5 !bg-zinc-950/60 !border-zinc-800/80 rounded-xl !text-white placeholder-zinc-600 focus:outline-none focus:!border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
                />
              </div>
            ) : null}

            <div className="space-y-1.5">
              <label htmlFor="auth-email" className="text-[10px] font-semibold !text-zinc-400 uppercase tracking-wider">
                Email
              </label>
              <input
                id="auth-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                required
                className="w-full px-3.5 py-2.5 !bg-zinc-950/60 !border-zinc-800/80 rounded-xl !text-white placeholder-zinc-600 focus:outline-none focus:!border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="auth-password" className="text-[10px] font-semibold !text-zinc-400 uppercase tracking-wider">
                Mật khẩu
              </label>
              <div className="relative">
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  required
                  minLength={8}
                  className="w-full pl-3.5 pr-11 py-2.5 !bg-zinc-950/60 !border-zinc-800/80 rounded-xl !text-white placeholder-zinc-600 focus:outline-none focus:!border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 !text-zinc-500 hover:!text-zinc-300 transition-colors p-0.5 cursor-pointer !bg-transparent !border-none !shadow-none !h-auto !min-h-0"
                >
                  {showPassword ? <EyeOffIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {isRegister ? (
              <div className="space-y-1.5">
                <label htmlFor="auth-confirm-password" className="text-[10px] font-semibold !text-zinc-400 uppercase tracking-wider">
                  Xác nhận mật khẩu
                </label>
                <input
                  id="auth-confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  className="w-full px-3.5 py-2.5 !bg-zinc-950/60 !border-zinc-800/80 rounded-xl !text-white placeholder-zinc-600 focus:outline-none focus:!border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
                />
              </div>
            ) : null}

            {isRegister ? (
              <div className="flex items-start gap-2.5 pt-1">
                <input
                  id="auth-terms"
                  type="checkbox"
                  checked={agreedTerms}
                  onChange={(event) => setAgreedTerms(event.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded border-zinc-800 bg-zinc-950 text-teal-500 focus:ring-teal-500/20 focus:ring-offset-0 transition-colors"
                />
                <label htmlFor="auth-terms" className="text-xs text-zinc-400 select-none leading-normal">
                  Tôi đồng ý với{' '}
                  <a href="#terms" onClick={(e) => e.preventDefault()} className="text-teal-400 hover:text-teal-300 hover:underline">
                    Điều khoản sử dụng
                  </a>{' '}
                  và{' '}
                  <a href="#privacy" onClick={(e) => e.preventDefault()} className="text-teal-400 hover:text-teal-300 hover:underline">
                    Chính sách bảo mật
                  </a>
                </label>
              </div>
            ) : null}

            {error ? (
              <div className="flex items-start gap-2.5 p-3 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-xs mt-4" role="alert">
                <AlertCircleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            ) : null}

            <button
              type="submit"
              disabled={isLoading}
              id="auth-submit-btn"
              className="w-full !h-11 flex items-center justify-center gap-2 rounded-xl !bg-gradient-to-r !from-teal-500 !to-emerald-600 hover:!from-teal-400 hover:!to-emerald-500 !text-white font-semibold text-sm shadow-lg shadow-teal-500/10 hover:shadow-teal-500/25 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:-translate-y-0.5 active:translate-y-0 cursor-pointer !border-none"
            >
              {isLoading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang xử lý...</span>
                </>
              ) : isRegister ? (
                'Tạo tài khoản'
              ) : (
                'Đăng nhập'
              )}
            </button>
          </form>

          {/* Card Footer */}
          <div className="mt-6 flex flex-col items-center gap-3">
            {!isRegister ? (
              <button 
                type="button" 
                id="auth-forgot-btn"
                className="text-xs !text-zinc-500 hover:!text-zinc-300 hover:underline transition-colors !bg-transparent !border-none !shadow-none !h-auto cursor-pointer"
              >
                Quên mật khẩu?
              </button>
            ) : null}
            <p className="text-xs text-zinc-400">
              {isRegister ? 'Đã có tài khoản? ' : 'Chưa có tài khoản? '}
              <button 
                type="button" 
                onClick={handleSwitchMode} 
                id="auth-toggle-mode-btn"
                className="!text-teal-400 hover:!text-teal-300 font-semibold hover:underline !bg-transparent !border-none !p-0 !shadow-none !h-auto ml-1 cursor-pointer"
              >
                {isRegister ? 'Đăng nhập' : 'Tạo tài khoản'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ─── Inline SVG Icons with spreads ─── */

function GoogleIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  )
}

function AppleIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C3.79 16.17 4.36 9.04 9.09 8.76c1.3.07 2.21.72 2.97.77.98-.2 1.92-.77 2.97-.7 1.25.1 2.2.58 2.82 1.49-2.59 1.54-1.97 4.93.4 5.87-.47 1.24-.68 1.84-1.2 2.94zM12.03 8.7c-.15-2.23 1.66-4.17 3.82-4.35.29 2.4-2.13 4.48-3.82 4.35z" />
    </svg>
  )
}

function EyeIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeOffIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function AlertCircleIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  )
}

function ShieldIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  )
}

function ChartIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function TargetIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
}

function BookIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}

function ArrowLeftIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  )
}
