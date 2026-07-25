import React from 'react'
import { motion } from 'framer-motion'
import NorthstarLogo from '../shared/components/NorthstarLogo'

const SURFACE_LABELS = {
  onboarding: 'Onboarding',
  home: 'Home',
  learning: 'Learn Hub',
  global_terminal: 'Market & Portfolio',
  news: 'News & Intelligence',
  news_economic_calendar: 'Lịch kinh tế',
  guided_investing: 'BCTC Analysis',
  pro_lab: 'Simulation Lab',
  backtest_studio: 'Backtest Studio',
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
      <div className="app-shell__masthead-brand-group">
        <motion.button
          type="button"
          className="app-shell__brand border-none bg-transparent p-0 flex items-center cursor-pointer outline-none focus:outline-none"
          onClick={onNavigateHome}
          title="Về Trang Chủ"
          aria-label="Về Trang Chủ"
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.97 }}
        >
          <NorthstarLogo size={28} />
        </motion.button>
        <p className="app-shell__surface">{SURFACE_LABELS[renderedView] || 'Workspace'}</p>
      </div>
      <div className="app-shell__masthead-actions">
        <span className={`app-shell__badge app-shell__badge--${tone}`}>
          {tone === 'pro' ? 'Simulation' : 'Education'}
        </span>
        {sessionId && !['home', 'onboarding', 'global_terminal'].includes(renderedView) ? (
          <motion.button
            type="button"
            className="button-ghost"
            onClick={onOpenTerminal}
            whileHover={{ scale: 1.05, y: -1 }}
            whileTap={{ scale: 0.95 }}
          >
            Market
          </motion.button>
        ) : null}
      </div>
    </header>
  )
}
