import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { trackAnalyticsEvent } from '../shared/analytics/trackEvent'
import ConnectedWorkspaceNav from '../shared/navigation/ConnectedWorkspaceNav'
import NavBar from './NavBar'
import AppShellRoutes from './AppShellRoutes'

const LazyNewsEconCalendarEmbed = lazy(() => import('../features/news/pages/NewsEconCalendarPage.jsx'))

const AUTHENTICATED_LANDING_VIEW = 'global_terminal'
const DEPRECATED_VIEW_ALIASES = {
  simulation_lab: 'pro_lab',
  insights: 'news',
  community: 'home',
  community_moderation: 'home',
  content_ops_admin: 'learning',
  pro_lab_admin: 'pro_lab',
  trust_safety_admin: 'pro_lab',
  analytics_admin: 'pro_lab',
  financial_statement_simulator: 'guided_investing',
  assignments: 'guided_investing',
}
const PUBLIC_VIEWS = new Set(['home', 'auth_login', 'auth_register'])

function readStoredSession() {
  if (typeof window === 'undefined') return ''
  try {
    return window.localStorage.getItem('public-beta.session_id') || ''
  } catch {
    return ''
  }
}

export default function AppShell({ initialView = 'home', view: controlledView, onNavigate }) {
  const [internalView, setInternalView] = useState(() => normalizeView(initialView))
  const view = normalizeView(controlledView || internalView)
  const [sessionId, setSessionId] = useState(() => readStoredSession())
  const [guidedFocusCard, setGuidedFocusCard] = useState('overview')
  const [learningFocus, setLearningFocus] = useState({ tab: 'courses', search: '' })
  const [proLabBacktestContext, setProLabBacktestContext] = useState({ selectedBlueprintId: '', workspace: null, accessToken: '' })
  const [pendingPostAuthView, setPendingPostAuthView] = useState('')
  const previousViewRef = useRef('')

  useEffect(() => {
    const savedSessionId = readStoredSession()
    const savedView = (typeof window !== 'undefined' && window.localStorage.getItem('public-beta.view')) || ''
    if (savedSessionId) {
      if (savedSessionId !== sessionId) setSessionId(savedSessionId)
      if (!controlledView) {
        const restoredView = savedView === 'learning_admin' ? initialView : (savedView || initialView)
        const nextView = normalizeView(restoredView === 'home' ? AUTHENTICATED_LANDING_VIEW : restoredView)
        if (onNavigate) onNavigate(nextView)
        else setInternalView(nextView)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (sessionId) window.localStorage.setItem('public-beta.session_id', sessionId)
    window.localStorage.setItem('public-beta.view', view)
  }, [sessionId, view])

  useEffect(() => {
    if (sessionId || isPublicView(view)) return
    setPendingPostAuthView(view)
    if (onNavigate) onNavigate('auth_login', { replace: true })
    else setInternalView('auth_login')
  }, [onNavigate, sessionId, view])

  useEffect(() => {
    if (sessionId && view === 'home') {
      const targetView = normalizeView(AUTHENTICATED_LANDING_VIEW)
      if (onNavigate) onNavigate(targetView, { replace: true })
      else setInternalView(targetView)
    }
  }, [onNavigate, sessionId, view])

  useEffect(() => {
    const previousView = previousViewRef.current
    trackAnalyticsEvent({
      event_name: 'app_view_changed',
      module: 'app_shell',
      surface: view,
      session_id: sessionId || window.localStorage.getItem('public-beta.session_id') || undefined,
      source_surface: previousView || undefined,
      target_surface: view,
      properties: { previous_view: previousView || null, current_view: view },
    })
    previousViewRef.current = view
  }, [sessionId, view])

  function setView(nextView, options) {
    const normalizedView = normalizeView(nextView)
    if (onNavigate) {
      onNavigate(normalizedView, options)
      return
    }
    setInternalView(normalizedView)
  }

  function openProtectedView(nextView, options) {
    const normalizedView = normalizeView(nextView)
    if (!sessionId) {
      setPendingPostAuthView(normalizedView)
      setView('auth_login')
      return
    }
    setView(normalizedView, options)
  }

  const isEconCalendarEmbed =
    view === 'news_economic_calendar' &&
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('embed') === '1'

  if (isEconCalendarEmbed) {
    return (
      <div className="app-shell app-shell--embed-calendar app-shell--public app-shell--transition-entered">
        <main className="app-shell__embed-calendar-main">
          <Suspense fallback={null}>
            <LazyNewsEconCalendarEmbed embed onBackToNews={() => openProtectedView('news')} />
          </Suspense>
        </main>
      </div>
    )
  }

  const tone = (view === 'pro_lab' || view === 'backtest_studio') ? 'pro' : 'public'
  const themeAttr = !isPublicView(view) && view !== 'guided_investing' ? 'dark' : 'light'
  const shellSkin = view === 'news_economic_calendar' ? 'news' : view

  const connectedNavActions = {
    openHome: () => sessionId ? setView(AUTHENTICATED_LANDING_VIEW) : setView('home'),
    openLearning: (focus = {}) => {
      setLearningFocus({ tab: focus.tab || 'courses', search: focus.search || '' })
      openProtectedView('learning')
    },
    openSimulationLab: () => openProtectedView('pro_lab'),
    openGuidedInvesting: (payload) => {
      setGuidedFocusCard(typeof payload === 'string' ? payload : 'overview')
      openProtectedView('guided_investing')
    },
    openGlobalTerminal: () => openProtectedView('global_terminal'),
    openNews: () => openProtectedView('news'),
    openProLab: () => openProtectedView('pro_lab'),
    openLogin: () => setView('auth_login'),
    openRegister: () => setView('auth_register'),
    openLogout: () => {
      window.localStorage.removeItem('public-beta.session_id')
      window.localStorage.removeItem('public-beta.user_profile')
      window.localStorage.removeItem('public-beta.view')
      setSessionId('')
      setPendingPostAuthView('')
      setView('home', { replace: true })
    },
  }

  const routeActions = {
    onBackHome: () => setView('home'),
    onOpenProLab: () => openProtectedView('pro_lab'),
    onOpenNews: () => openProtectedView('news'),
    onOpenGlobalTerminal: () => openProtectedView('global_terminal'),
    onOpenLearning: connectedNavActions.openLearning,
    onOpenGuidedInvesting: connectedNavActions.openGuidedInvesting,
    onOpenLogin: () => setView('auth_login'),
    onOpenOnboarding: () => openProtectedView('onboarding'),
    onBackProLab: () => setView('pro_lab'),
    onOpenBacktestStudio: (context = {}) => {
      setProLabBacktestContext((c) => ({
        selectedBlueprintId: context.selectedBlueprintId || c.selectedBlueprintId || '',
        workspace: context.workspace || c.workspace || null,
        accessToken: context.accessToken || c.accessToken || '',
      }))
      setView('backtest_studio')
    },
    onAuthSuccess: (payload) => {
      setSessionId(payload.session_id)
      setView(pendingPostAuthView || AUTHENTICATED_LANDING_VIEW)
      setPendingPostAuthView('')
    },
    onAuthSwitchMode: (mode) => setView(mode === 'register' ? 'auth_register' : 'auth_login'),
    onOnboardingCompleted: (payload) => {
      setSessionId(payload.session_id)
      setView(AUTHENTICATED_LANDING_VIEW)
    },
  }

  return (
    <div className={`app-shell app-shell--${shellSkin.replaceAll('_', '-')} app-shell--${tone} ${themeAttr}`} data-theme={themeAttr}>
      <div className="app-shell__ambient app-shell__ambient--one" />
      <div className="app-shell__ambient app-shell__ambient--two" />
      <div className="app-shell__frame">
        <NavBar renderedView={view} tone={tone} sessionId={sessionId} onNavigateHome={() => setView('home')} onOpenTerminal={() => openProtectedView('global_terminal')} />
        <main className="app-shell__content">
          <ConnectedWorkspaceNav currentView={view} sessionId={sessionId} actions={connectedNavActions} showTabs={Boolean(sessionId)} />
          <motion.div
            key={view}
            className="surface-panel"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
          >
            <AppShellRoutes
              renderedView={view}
              sessionId={sessionId}
              learningFocus={learningFocus}
              guidedFocusCard={guidedFocusCard}
              proLabBacktestContext={proLabBacktestContext}
              actions={routeActions}
            />
          </motion.div>
        </main>
      </div>
    </div>
  )
}

function normalizeView(view) {
  return DEPRECATED_VIEW_ALIASES[view] || view
}

function isPublicView(view) {
  return PUBLIC_VIEWS.has(normalizeView(view))
}
