import { useEffect, useRef, useState } from 'react'

import { trackAnalyticsEvent } from '../analytics/trackEvent'

function ChevronDownIcon({ className }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
  )
}

function MapIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
      <line x1="9" y1="3" x2="9" y2="18"></line>
      <line x1="15" y1="6" x2="15" y2="21"></line>
    </svg>
  )
}

function LibraryIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
    </svg>
  )
}

function RobotIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="2"></rect>
      <circle cx="12" cy="5" r="2"></circle>
      <path d="M12 7v4"></path>
      <line x1="8" y1="16" x2="8" y2="16"></line>
      <line x1="16" y1="16" x2="16" y2="16"></line>
    </svg>
  )
}

function BarChartIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"></line>
      <line x1="12" y1="20" x2="12" y2="4"></line>
      <line x1="6" y1="20" x2="6" y2="14"></line>
    </svg>
  )
}

function PieChartIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
      <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
    </svg>
  )
}

function DollarIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23"></line>
      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
    </svg>
  )
}

function AlertTriangleIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
      <line x1="12" y1="9" x2="12" y2="13"></line>
      <line x1="12" y1="17" x2="12.01" y2="17"></line>
    </svg>
  )
}

function FileTextIcon({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </svg>
  )
}

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
    dropdown: [
      { id: 'path', label: 'Lộ trình', icon: MapIcon },
      { id: 'library', label: 'Thư viện', icon: LibraryIcon },
      { id: 'tutor', label: 'Hỏi AI', icon: RobotIcon },
    ],
  },
  {
    id: 'guided_investing',
    label: 'BCTC',
    short: 'Financial analysis',
    group: 'analysis',
    action: 'openGuidedInvesting',
    dropdown: [
      { id: 'income', label: 'Kết quả kinh doanh', icon: BarChartIcon },
      { id: 'balance', label: 'Bảng cân đối', icon: PieChartIcon },
      { id: 'cash-flow', label: 'Lưu chuyển tiền', icon: DollarIcon },
      { id: 'ratios', label: 'Chỉ số', icon: BarChartIcon },
      { id: 'horizontal', label: 'Phân tích ngang', icon: BarChartIcon },
      { id: 'vertical', label: 'Phân tích dọc', icon: BarChartIcon },
      { id: 'risk', label: 'Cảnh báo rủi ro', icon: AlertTriangleIcon },
      { id: 'report', label: 'Báo cáo', icon: FileTextIcon },
    ],
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
      <button
        type="button"
        className="connected-nav__brand-btn"
        onClick={() => actions?.openHome?.()}
        title="Về Trang Chủ"
        aria-label="Về Trang Chủ"
      >
        <i className="connected-nav__mark" aria-hidden="true" />
        <strong>Northstar Finance</strong>
      </button>
      <div className="connected-nav__tabs">
        {showTabs ? FLOW.map((item) => (
          <div key={item.id} className="connected-nav__tab-wrapper">
            <button
              type="button"
              className={`connected-nav__tab ${(currentView === item.id || (item.id === 'news' && currentView === 'news_economic_calendar')) ? 'connected-nav__tab--active' : ''}`}
              onClick={() => open(item)}
            >
              {item.label}
              {item.id === 'pro_lab' ? <span className="connected-nav__pro">PRO</span> : null}
              {item.dropdown ? <ChevronDownIcon className="connected-nav__dropdown-icon" /> : null}
            </button>
            {item.dropdown && (
              <div className="connected-nav__dropdown">
                {item.dropdown.map(dropItem => {
                  const Icon = dropItem.icon;
                  return (
                    <button 
                      key={dropItem.id} 
                      type="button"
                      className="connected-nav__dropdown-item"
                      onClick={(e) => {
                        e.stopPropagation();
                        open({ ...item, payload: dropItem.id });
                      }}
                    >
                      {Icon && <Icon className="connected-nav__dropdown-item-icon" />}
                      {dropItem.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
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
