import { trackAnalyticsEvent } from '../analytics/trackEvent'

const FLOW = [
  {
    id: 'global_terminal',
    label: 'Terminal',
    short: 'Live market board',
    group: 'market',
    action: 'openGlobalTerminal',
  },
  {
    id: 'news',
    label: 'News',
    short: 'Market narrative',
    group: 'market',
    action: 'openNews',
  },
  {
    id: 'insights',
    label: 'Insights',
    short: 'What changed',
    group: 'intelligence',
    action: 'openInsights',
  },
  {
    id: 'guided_investing',
    label: 'BCTC',
    short: 'Financial analysis',
    group: 'intelligence',
    action: 'openGuidedInvesting',
    payload: 'market_context',
  },
  {
    id: 'learning',
    label: 'Learn',
    short: 'Understand concepts',
    group: 'education',
    action: 'openLearning',
  },
  {
    id: 'financial_health',
    label: 'Health',
    short: 'Personal baseline',
    group: 'personal',
    action: 'openFinancialHealth',
  },
  {
    id: 'goals',
    label: 'Goals',
    short: 'Plan next step',
    group: 'personal',
    action: 'openGoals',
    payload: '',
  },
  {
    id: 'community',
    label: 'Community',
    short: 'Learn with guardrails',
    group: 'retention',
    action: 'openCommunity',
    payload: '',
  },
  {
    id: 'pro_lab',
    label: 'Pro Lab',
    short: 'Research sandbox',
    group: 'pro',
    action: 'openProLab',
  },
]

export default function ConnectedWorkspaceNav({ currentView, sessionId, actions }) {
  if (currentView?.includes('admin') || currentView === 'backtest_studio' || currentView === 'global_terminal') return null

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

  return (
    <nav className="connected-nav" aria-label="Connected product navigation">
      <div className="connected-nav__brand">
        <i className="connected-nav__mark" aria-hidden="true" />
        <strong>Northstar Finance</strong>
      </div>
      <div className="connected-nav__tabs">
        <button
          type="button"
          className={`connected-nav__tab ${currentView === 'home' ? 'connected-nav__tab--active' : ''}`}
          onClick={() => actions?.openHome?.()}
        >
          Home
        </button>
        {FLOW.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`connected-nav__tab ${currentView === item.id ? 'connected-nav__tab--active' : ''}`}
            onClick={() => open(item)}
          >
            {item.label}
            {item.id === 'pro_lab' ? <span className="connected-nav__pro">PRO</span> : null}
          </button>
        ))}
      </div>
      {!sessionId ? (
        <button
          type="button"
          className="connected-nav__login"
          onClick={() => actions?.openLogin?.()}
        >
          Đăng nhập
        </button>
      ) : (
        <button
          type="button"
          className="connected-nav__avatar"
          onClick={() => actions?.openLogin?.()}
          aria-label="Tài khoản"
        >
          {getInitial(sessionId)}
        </button>
      )}
    </nav>
  )
}

function getInitial(sessionId) {
  try {
    const profile = JSON.parse(window.localStorage.getItem('public-beta.user_profile') || 'null')
    if (profile?.name) return profile.name.charAt(0).toUpperCase()
    if (profile?.email) return profile.email.charAt(0).toUpperCase()
  } catch { /* ignore */ }
  return 'U'
}
