import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

import { NAV_FLOW } from '../../app/productRegistry'
import { trackAnalyticsEvent } from '../analytics/trackEvent'
import NorthstarLogo from '../components/NorthstarLogo'

const FLOW = NAV_FLOW.map((domain) => ({
  id: domain.view,
  label: domain.label,
  mobileLabel: domain.mobileLabel,
  short: domain.short,
  action: domain.navAction,
}))

export default function ConnectedWorkspaceNav({ currentView, sessionId, actions, showTabs = true }) {
  const [isScrolled, setIsScrolled] = useState(() => getScrollY() > 18)
  const [isHidden, setIsHidden] = useState(false)
  const [hoveredTab, setHoveredTab] = useState(null)
  const lastScrollYRef = useRef(getScrollY())

  useEffect(() => {
    function handleScroll() {
      const nextScrollY = getScrollY()
      const delta = nextScrollY - lastScrollYRef.current
      setIsScrolled(nextScrollY > 18)
      setIsHidden(nextScrollY > 140 && delta > 6)
      lastScrollYRef.current = nextScrollY
    }

    const frame = window.requestAnimationFrame(() => {
      setIsHidden(false)
      lastScrollYRef.current = getScrollY()
      setIsScrolled(getScrollY() > 18)
    })
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      window.cancelAnimationFrame(frame)
      window.removeEventListener('scroll', handleScroll)
    }
  }, [currentView])

  if (currentView?.includes('admin') || currentView === 'backtest_studio') return null

  function open(item) {
    const handler = actions?.[item.action]
    if (!handler) return
    trackAnalyticsEvent({
      event_name: 'connected_nav_clicked',
      module: 'app_shell',
      surface: currentView,
      session_id: sessionId || undefined,
      target_surface: item.id,
      properties: {
        source_surface: currentView,
        target_group: item.group,
        target_label: item.label,
      },
    })
    handler(item.payload)
  }

  function revealNav() {
    setIsHidden(false)
  }

  return (
    <div
      className={`connected-nav-shell ${isHidden ? 'connected-nav-shell--hidden' : ''}`}
      onMouseEnter={revealNav}
      onFocus={revealNav}
    >
      <nav className={`connected-nav ${isScrolled ? 'connected-nav--scrolled' : 'connected-nav--top'}`} aria-label="Connected product navigation">
      <motion.button
        type="button"
        className="connected-nav__brand-btn border-none bg-transparent p-0 flex items-center cursor-pointer outline-none focus:outline-none"
        onClick={() => actions?.openHome?.()}
        title="Về Trang Chủ"
        aria-label="Về Trang Chủ"
        whileHover={{ scale: 1.04 }}
        whileTap={{ scale: 0.97 }}
      >
        <NorthstarLogo size={28} />
      </motion.button>
      <div className="connected-nav__tabs">
        {showTabs ? FLOW.map((item) => {
          const isActive = currentView === item.id || (item.id === 'news' && currentView === 'news_economic_calendar')
          const isHovered = hoveredTab === item.id
          return (
            <div
              key={item.id}
              className="connected-nav__tab-wrapper"
              onMouseEnter={() => setHoveredTab(item.id)}
              onMouseLeave={() => setHoveredTab(null)}
            >
              <motion.button
                type="button"
                className={`connected-nav__tab ${isActive ? 'connected-nav__tab--active' : ''}`}
                onClick={() => open(item)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                transition={{ duration: 0.12 }}
              >
                {isHovered && !isActive && (
                  <motion.span
                    layoutId="hoverNavTabBg"
                    className="connected-nav__hover-bg"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                  />
                )}
                <span className="connected-nav__label connected-nav__label--desktop">{item.label}</span>
                <span className="connected-nav__label connected-nav__label--mobile">{item.mobileLabel || item.label}</span>
                {isActive && (
                  <motion.span
                    layoutId="activeNavTabIndicator"
                    className="connected-nav__active-indicator"
                    transition={{ type: 'spring', stiffness: 380, damping: 28 }}
                  />
                )}
              </motion.button>
            </div>
          )
        }) : null}
      </div>
      {!sessionId ? (
        <div className="connected-nav__auth-actions">
          <motion.button
            type="button"
            className="connected-nav__login connected-nav__login--ghost"
            onClick={() => actions?.openLogin?.()}
            whileHover={{ scale: 1.04, y: -1 }}
            whileTap={{ scale: 0.96 }}
          >
            Đăng nhập
          </motion.button>
          <motion.button
            type="button"
            className="connected-nav__login"
            onClick={() => actions?.openRegister?.()}
            whileHover={{ scale: 1.04, y: -1 }}
            whileTap={{ scale: 0.96 }}
          >
            Tạo tài khoản
          </motion.button>
        </div>
      ) : (
        <div className="connected-nav__account">
          <motion.button
            type="button"
            className="connected-nav__avatar"
            onClick={() => actions?.openGlobalTerminal?.()}
            aria-label="Tài khoản"
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
          >
            {getInitial(sessionId)}
          </motion.button>
          <motion.button
            type="button"
            className="connected-nav__logout"
            onClick={() => actions?.openLogout?.()}
            whileHover={{ scale: 1.04, y: -1 }}
            whileTap={{ scale: 0.96 }}
          >
            Đăng xuất
          </motion.button>
        </div>
      )}
      </nav>
    </div>
  )
}

function getScrollY() {
  if (typeof window === 'undefined') return 0
  return window.scrollY || window.document?.documentElement?.scrollTop || 0
}

function getInitial(sessionId) {
  try {
    const profile = JSON.parse(window.localStorage.getItem('public-beta.user_profile') || 'null')
    if (profile?.name) return profile.name.charAt(0).toUpperCase()
    if (profile?.email) return profile.email.charAt(0).toUpperCase()
  } catch { /* ignore */ }
  if (sessionId) return String(sessionId).charAt(0).toUpperCase()
  return 'U'
}
