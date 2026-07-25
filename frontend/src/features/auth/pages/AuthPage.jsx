import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  BarChart3,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Eye,
  EyeOff,
  Globe,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  User,
  Zap,
} from 'lucide-react'

import { useAuth } from '..'
import Auth3DObjectCanvas from '../components/Auth3DObjectCanvas'
import NorthstarLogo from '../../../shared/components/NorthstarLogo'
import './auth.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

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

const SHOWCASE_ITEMS = [
  {
    id: 'market_terminal',
    label: '01. Trợ Lý AI',
    badge: 'AI-POWERED INSIGHTS',
    title: 'Trợ Lý AI Phân Tích Dòng Tiền 24/7',
    subtitle: 'Tự động tổng hợp thông tin thị trường, phát hiện biến động bất thường và gợi ý chiến lược tối ưu.',
    icon: Sparkles,
    accentColor: 'from-emerald-400 to-teal-500',
    widget: (
      <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-800/50 backdrop-blur-md shadow-2xl space-y-3 w-full max-w-md">
        <div className="flex items-center justify-between border-b border-zinc-800/60 pb-2.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold text-white tracking-tight">AI Intelligence Radar</span>
          </div>
          <span className="text-[10px] font-semibold text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded-full border border-teal-500/20">
            Active 24/7
          </span>
        </div>

        {/* Marketing Feature Bullets */}
        <div className="space-y-2 text-[11px]">
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
            <span>Phân tích tâm lý tin tức & sự kiện vĩ mô</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Cảnh báo rủi ro danh mục tự động</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>Tổng hợp báo cáo từ 20+ CTCK uy tín</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'bctc_lab',
    label: '02. BCTC Lab',
    badge: 'INTERACTIVE FINANCIAL LAB',
    title: 'Phòng Lab Mô Phỏng & Bóc Tách BCTC',
    subtitle: 'Chuẩn hóa dữ liệu báo cáo tài chính 1,000+ doanh nghiệp niêm yết thành mô hình trực quan.',
    icon: BarChart3,
    accentColor: 'from-teal-400 to-indigo-500',
    widget: (
      <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-800/50 backdrop-blur-md shadow-2xl space-y-3 w-full max-w-md">
        <div className="flex items-center justify-between border-b border-zinc-800/60 pb-2.5">
          <span className="text-xs font-bold text-white">Tính Năng BCTC Simulator</span>
          <span className="text-[10px] font-mono font-semibold text-teal-400">1,000+ Doanh nghiệp</span>
        </div>

        {/* Feature Highlights */}
        <div className="space-y-2 text-[11px]">
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
            <span>Mô hình hóa Du Pont 5 bước chuyên sâu</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Dự phóng dòng tiền & định giá P/E, P/B, DCF</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>So sánh sức khỏe tài chính cùng ngành</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'backtest_studio',
    label: '03. Backtest',
    badge: 'QUANTITATIVE STRATEGY LAB',
    title: 'Mô Phỏng & Kiểm Thử Thuật Toán',
    subtitle: 'Kiểm thử chiến lược đầu tư với 10,000+ kịch bản thị trường giả lập trước khi giao dịch thực tế.',
    icon: Cpu,
    accentColor: 'from-indigo-400 to-purple-500',
    widget: (
      <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-800/50 backdrop-blur-md shadow-2xl space-y-3 w-full max-w-md">
        <div className="flex items-center justify-between border-b border-zinc-800/60 pb-2.5">
          <span className="text-xs font-bold text-white">Kiểm Thử Thuật Toán Giao Dịch</span>
          <span className="text-[10px] font-mono text-indigo-400">Monte Carlo Engine</span>
        </div>

        {/* Feature Highlights */}
        <div className="space-y-2 text-[11px]">
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>Đo lường Sharpe Ratio, Win Rate & Max Drawdown</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
            <span>Mô phỏng 10,000+ kịch bản thị trường biến động</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Tối ưu hóa tham số chiến lược tự động</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'news_radar',
    label: '04. Terminal',
    badge: 'INSTITUTIONAL TERMINAL',
    title: 'Bảng Giá & Dữ Liệu Thời Gian Thực',
    subtitle: 'Trải nghiệm bảng giá đa tài sản HOSE, HNX, Phái sinh với độ trễ thấp chuẩn công ty chứng khoán.',
    icon: TrendingUp,
    accentColor: 'from-amber-400 to-teal-400',
    widget: (
      <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-800/50 backdrop-blur-md shadow-2xl space-y-3 w-full max-w-md">
        <div className="flex items-center justify-between border-b border-zinc-800/60 pb-2.5">
          <span className="text-xs font-bold text-white">Dữ Liệu Khớp Lệnh Real-Time</span>
          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            Latency &lt; 50ms
          </span>
        </div>

        {/* Feature Highlights */}
        <div className="space-y-2 text-[11px]">
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Theo dõi độ sâu sổ lệnh & lực mua/bán</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
            <span>100% Học thuật & phân tích — Không phím lệnh</span>
          </div>
          <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-zinc-200 backdrop-blur-sm">
            <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Tùy chỉnh Workspace phân tích chuyên sâu</span>
          </div>
        </div>
      </div>
    ),
  },
]

const SHOWCASE_INTERVAL_MS = 5000

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
  const [showcaseIndex, setShowcaseIndex] = useState(0)

  // Auto-advance showcase slides every 5s
  useEffect(() => {
    const timer = setInterval(() => {
      setShowcaseIndex((prev) => (prev + 1) % SHOWCASE_ITEMS.length)
    }, SHOWCASE_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [])

  const currentShowcase = SHOWCASE_ITEMS[showcaseIndex]

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
            try {
              if (!response?.credential) {
                setError('Không nhận được thông tin xác thực từ Google.')
                return
              }
              const result = await loginWithGoogle(response.credential)
              if (result) onAuthSuccess?.(result)
            } catch (err) {
              if (!cancelled) setError(err.message || 'Đăng nhập Google không thành công.')
            }
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
      className="relative min-h-screen w-full grid grid-cols-1 lg:grid-cols-2 bg-[#050811] text-zinc-100 overflow-hidden font-sans dark" 
      aria-label={isRegister ? 'Đăng ký tài khoản' : 'Đăng nhập tài khoản'}
      data-theme="dark"
    >
      {/* Ambient Background Radial Glows */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -top-[15%] -left-[10%] w-[65%] h-[55%] rounded-full bg-gradient-to-br from-teal-500/12 via-emerald-500/5 to-transparent blur-[120px]" />
        <div className="absolute bottom-[-15%] right-[-10%] w-[65%] h-[55%] rounded-full bg-gradient-to-br from-indigo-500/12 via-purple-500/5 to-transparent blur-[140px]" />
      </div>

      {/* ─── Left Marketing Showcase — Single Unified 3D Display ─── */}
      <div className="hidden lg:flex flex-col justify-between p-10 xl:p-14 bg-zinc-950/50 border-r border-zinc-800/40 relative overflow-hidden backdrop-blur-2xl">
        {/* Full-Bleed Morphing 3D Canvas Background */}
        <div className="absolute inset-0 z-0">
          <Auth3DObjectCanvas activeTab={currentShowcase.id} />
          <div className="absolute inset-0 bg-gradient-to-b from-[#050811]/80 via-[#050811]/40 to-[#050811]/85 pointer-events-none" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#050811]/50 via-transparent to-[#050811]/50 pointer-events-none" />
        </div>

        {/* Ambient Glows */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
          <div className="absolute top-[20%] -left-[20%] w-[100%] h-[50%] rounded-full bg-teal-500/10 blur-[100px] animate-pulse duration-[9s]" />
          <div className="absolute bottom-[15%] -right-[20%] w-[100%] h-[50%] rounded-full bg-indigo-500/10 blur-[110px] animate-pulse duration-[11s]" />
        </div>

        {/* Brand Header */}
        <motion.div
          className="relative z-10 flex items-center justify-between"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div onClick={onNavigateHome}>
            <NorthstarLogo size={36} />
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-zinc-800/80 text-[11px] font-medium text-zinc-400 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>3D Interactive Engine</span>
          </div>
        </motion.div>

        {/* Unified 3D Stage Interactive Display Content */}
        <div className="relative z-10 my-auto py-6 space-y-6 max-w-lg">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentShowcase.id}
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.97 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className="space-y-5"
            >
              {/* Feature Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/25 text-teal-300 text-xs font-medium backdrop-blur-md">
                <currentShowcase.icon className="w-3.5 h-3.5 text-teal-400" />
                <span>{currentShowcase.badge}</span>
              </div>

              {/* Main Headline Title & Subtitle */}
              <div className="space-y-2">
                <h1 className="text-3xl xl:text-4xl font-extrabold tracking-tight text-white leading-tight">
                  {currentShowcase.title}
                </h1>
                <p className="text-zinc-400 text-xs xl:text-sm leading-relaxed max-w-md">
                  {currentShowcase.subtitle}
                </p>
              </div>

              {/* Glassmorphic Feature Card Overlay */}
              <div className="w-full">
                {currentShowcase.widget}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Integrated Slide Indicators */}
          <div className="flex items-center gap-2 pt-2">
            {SHOWCASE_ITEMS.map((item, idx) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setShowcaseIndex(idx)}
                aria-label={`Chuyển tới slide ${idx + 1}`}
                className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                  showcaseIndex === idx
                    ? 'w-7 bg-teal-400'
                    : 'w-2 bg-zinc-700 hover:bg-zinc-500'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Hero Footer */}
        <div className="relative z-10 text-[11px] text-zinc-500 flex justify-between items-center w-full pt-4 border-t border-zinc-900/80">
          <span>© 2026 Northstar Finance Lab</span>
          <span className="flex items-center gap-1.5 text-teal-400/90 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            System Live • 25,000+ Active Members
          </span>
        </div>
      </div>

      {/* ─── Right Auth Form ─── */}
      <div className="flex flex-col justify-center items-center p-6 sm:p-12 md:p-16 relative bg-[#050811]">
        <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
          <div className="absolute top-[10%] right-[10%] w-[55%] h-[45%] rounded-full bg-gradient-to-br from-teal-500/8 to-transparent blur-[120px]" />
        </div>

        {/* Centered Form Container */}
        <AnimatePresence mode="wait">
          <motion.div 
            key={mode}
            className="relative z-10 w-full max-w-md"
            initial={{ opacity: 0, x: isRegister ? 16 : -16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: isRegister ? -16 : 16 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            {/* Back to Home Button */}
            <motion.button 
              type="button" 
              onClick={onNavigateHome} 
              id="auth-back-btn"
              className="group mb-8 inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold text-zinc-400 hover:text-zinc-100 bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 rounded-xl transition-all duration-200 cursor-pointer backdrop-blur-md shadow-sm"
              whileHover={{ x: -2 }}
              whileTap={{ scale: 0.97 }}
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform text-teal-400" />
              <span>Về trang chủ</span>
            </motion.button>

            {/* Header */}
            <div className="mb-6 space-y-1.5">
              <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                {isRegister ? 'Tạo tài khoản mới' : 'Chào mừng trở lại'}
                <Sparkles className="w-5 h-5 text-teal-400" />
              </h2>
              <p className="text-xs text-zinc-400 leading-relaxed">
                {isRegister
                  ? 'Đăng ký tài khoản Northstar Finance để cá nhân hóa trải nghiệm học và phân tích.'
                  : 'Đăng nhập để tiếp tục mở workspace tài chính cá nhân của bạn.'}
              </p>
            </div>

            {/* Google SSO Container */}
            <div className="mb-6 flex justify-center w-full">
              <div 
                className="google-btn-container w-full h-[40px] rounded-xl overflow-hidden border border-zinc-800 hover:border-zinc-700 bg-white transition-colors shadow-sm" 
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
                <span className="px-3 bg-[#050811] text-zinc-400 rounded-full border border-zinc-800/60 py-0.5 font-semibold text-[10px]">
                  Hoặc đăng nhập bằng Email
                </span>
              </div>
            </div>

            {/* Main Auth Form */}
            <form className="space-y-4" onSubmit={handleSubmit} noValidate>
              {isRegister ? (
                <div className="space-y-1.5">
                  <label htmlFor="auth-name" className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <User className="w-3 h-3 text-teal-400" />
                    <span>Họ và tên</span>
                  </label>
                  <div className="relative">
                    <input
                      id="auth-name"
                      type="text"
                      placeholder="Nguyễn Văn A"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      autoComplete="name"
                      required
                      className="w-full px-3.5 py-2.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
                    />
                  </div>
                </div>
              ) : null}

              <div className="space-y-1.5">
                <label htmlFor="auth-email" className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Mail className="w-3 h-3 text-teal-400" />
                  <span>Email</span>
                </label>
                <input
                  id="auth-email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                  className="w-full px-3.5 py-2.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="auth-password" className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="w-3 h-3 text-teal-400" />
                  <span>Mật khẩu</span>
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
                    className="w-full pl-3.5 pr-11 py-2.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors p-0.5 cursor-pointer bg-transparent border-none shadow-none h-auto min-h-0"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {isRegister ? (
                <div className="space-y-1.5">
                  <label htmlFor="auth-confirm-password" className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Lock className="w-3 h-3 text-teal-400" />
                    <span>Xác nhận mật khẩu</span>
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
                    className="w-full px-3.5 py-2.5 bg-zinc-950/80 border border-zinc-800/80 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:border-teal-500/80 focus:ring-2 focus:ring-teal-500/10 transition-all duration-200 text-sm"
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
                    className="mt-0.5 w-4 h-4 rounded border-zinc-800 bg-zinc-950 text-teal-500 focus:ring-teal-500/20 focus:ring-offset-0 transition-colors cursor-pointer"
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
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{error}</span>
                </div>
              ) : null}

              <motion.button
                type="submit"
                disabled={isLoading}
                id="auth-submit-btn"
                className="w-full h-11 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-teal-500 via-emerald-500 to-teal-600 hover:from-teal-400 hover:to-emerald-400 text-white font-semibold text-sm shadow-lg shadow-teal-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer border-none"
                whileHover={{ scale: 1.015, y: -1 }}
                whileTap={{ scale: 0.985 }}
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
              </motion.button>
            </form>

            {/* Footer Options */}
            <div className="mt-6 flex flex-col items-center gap-3">
              {!isRegister ? (
                <button 
                  type="button" 
                  id="auth-forgot-btn"
                  className="text-xs text-zinc-500 hover:text-zinc-300 hover:underline transition-colors bg-transparent border-none shadow-none h-auto cursor-pointer"
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
                  className="text-teal-400 hover:text-teal-300 font-semibold hover:underline bg-transparent border-none p-0 shadow-none h-auto ml-1 cursor-pointer"
                >
                  {isRegister ? 'Đăng nhập' : 'Tạo tài khoản'}
                </button>
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}

