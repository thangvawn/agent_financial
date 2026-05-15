import { useEffect, useRef, useState } from 'react'

import { trackAnalyticsEvent } from '../analytics/trackEvent'

const FLOW = [
  {
    id: 'global_terminal',
    label: 'Global Terminal',
    short: 'Cross-asset market desk',
    group: 'analysis',
    action: 'openGlobalTerminal',
  },
  {
    id: 'learning',
    label: 'Learn',
    short: 'Short lessons',
    group: 'education',
    action: 'openLearning',
  },
  {
    id: 'guided_investing',
    label: 'BCTC',
    short: 'Financial statement analysis',
    group: 'analysis',
    action: 'openGuidedInvesting',
    payload: 'market_context',
  },
  {
    id: 'news',
    label: 'News',
    short: 'Market narrative',
    group: 'analysis',
    action: 'openNews',
  },
  {
    id: 'pro_lab',
    label: 'Pro Lab',
    short: 'Research sandbox',
    group: 'pro',
    action: 'openProLab',
  },
]

export default function ConnectedWorkspaceNav({ currentView, sessionId, actions, showTabs = true }) {
  const [isScrolled, setIsScrolled] = useState(() => getScrollY() > 18)
  const [isHidden, setIsHidden] = useState(false)
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
      <div className="connected-nav__brand">
        <i className="connected-nav__mark" aria-hidden="true" />
        <strong>Northstar Finance</strong>
      </div>
      <div className="connected-nav__tabs">
        {showTabs ? FLOW.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`connected-nav__tab ${(currentView === item.id || (item.id === 'news' && currentView === 'news_economic_calendar')) ? 'connected-nav__tab--active' : ''}`}
            onClick={() => open(item)}
          >
            {item.label}
            {item.id === 'pro_lab' ? <span className="connected-nav__pro">PRO</span> : null}
          </button>
        )) : null}
      </div>
      {!sessionId ? (
        <div className="connected-nav__auth-actions">
          <button
            type="button"
            className="connected-nav__login connected-nav__login--ghost"
            onClick={() => actions?.openLogin?.()}
          >
            Đăng nhập
          </button>
          <button
            type="button"
            className="connected-nav__login"
            onClick={() => actions?.openRegister?.()}
          >
            Tạo tài khoản
          </button>
        </div>
      ) : (
        <div className="connected-nav__account">
          <button
            type="button"
            className="connected-nav__avatar"
            onClick={() => actions?.openGlobalTerminal?.()}
            aria-label="Tài khoản"
          >
            {getInitial(sessionId)}
          </button>
          <button
            type="button"
            className="connected-nav__logout"
            onClick={() => actions?.openLogout?.()}
          >
            Đăng xuất
          </button>
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
