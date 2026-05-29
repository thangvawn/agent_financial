import React from 'react'

const SURFACE_LABELS = {
  onboarding: 'Onboarding',
  home: 'Home',
  learning: 'Learn Hub',
  financial_statement_simulator: 'Financial Statement Simulator',
  assignments: 'Assignments',
  content_ops_admin: 'Content Ops',
  global_terminal: 'Global Terminal',
  news: 'News Desk',
  news_economic_calendar: 'Lịch kinh tế',
  community: 'Community',
  community_moderation: 'Community Moderation',
  guided_investing: 'BCTC Analysis',
  insights: 'Insights',
  pro_lab: 'Pro Lab',
  backtest_studio: 'Backtest Studio',
  pro_lab_admin: 'Pro Lab Admin',
  trust_safety_admin: 'Trust & Safety',
  analytics_admin: 'Analytics & Ops',
  auth_login: 'Đăng nhập',
  auth_register: 'Đăng ký',
}

export default function NavBar({
  renderedView,
  tone,
  sessionId,
  onNavigateHome,
  onOpenTerminal,
}) {
  return (
    <header className="app-shell__masthead">
      <div>
        <button
          type="button"
          className="app-shell__brand"
          onClick={onNavigateHome}
          title="Về Trang Chủ"
          aria-label="Về Trang Chủ"
        >
          Northstar Finance Lab
        </button>
        <p className="app-shell__surface">{SURFACE_LABELS[renderedView] || 'Workspace'}</p>
      </div>
      <div className="app-shell__masthead-actions">
        <span className={`app-shell__badge app-shell__badge--${tone}`}>
          {tone === 'operator' ? 'Instructor / Admin' : tone === 'pro' ? 'Paper Research' : 'Education'}
        </span>
        {sessionId && !['home', 'onboarding', 'global_terminal'].includes(renderedView) ? (
          <button type="button" className="button-ghost" onClick={onOpenTerminal}>
            Terminal
          </button>
        ) : null}
      </div>
    </header>
  )
}
