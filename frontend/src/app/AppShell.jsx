import { useEffect, useRef, useState } from 'react'
import { animate, stagger } from 'animejs'
import { AnimatePresence, motion } from 'framer-motion'

import {
  AuthPage,
  GuidedInvestingPage,
  HomePage,
  LearningHomePage,
  MarketPortfolioPage,
  NewsEconCalendarPage,
  NewsPage,
  OnboardingPage,
  ProLabBacktestStudioPage,
  ProLabPage,
} from '../features'
import { trackAnalyticsEvent } from '../shared/analytics/trackEvent'
import ConnectedWorkspaceNav from '../shared/navigation/ConnectedWorkspaceNav'
import NavBar from './NavBar'

const PAGE_TRANSITION_MS = 200
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
  const [renderedView, setRenderedView] = useState(() => view)
  const [transitionPhase, setTransitionPhase] = useState('entered')
  const [sessionId, setSessionId] = useState(() => readStoredSession())
  const [guidedFocusCard, setGuidedFocusCard] = useState('overview')
  const [proLabBacktestContext, setProLabBacktestContext] = useState({ selectedBlueprintId: '', workspace: null, accessToken: '' })
  const [pendingPostAuthView, setPendingPostAuthView] = useState('')
  const previousViewRef = useRef('')
  const surfacePanelRef = useRef(null)

  useEffect(() => {
    if (view === renderedView) return undefined
    if (prefersReducedMotion()) {
      setRenderedView(view)
      setTransitionPhase('entered')
      return undefined
    }

    setTransitionPhase('exiting')
    const exitTimer = window.setTimeout(() => {
      setRenderedView(view)
      setTransitionPhase('entering')
      window.requestAnimationFrame(() => setTransitionPhase('entered'))
    }, PAGE_TRANSITION_MS)

    return () => window.clearTimeout(exitTimer)
  }, [renderedView, view])

  useEffect(() => {
    if (!surfacePanelRef.current) return
    if (prefersReducedMotion()) return

    if (transitionPhase === 'exiting') {
      animate(surfacePanelRef.current, { opacity: 0, y: 12, duration: 0.15, ease: 'inQuad' })
    } else if (transitionPhase === 'entering') {
      animate(surfacePanelRef.current, { opacity: [0, 1], duration: 0.2, ease: 'outQuad' })
      const targets = Array.from(surfacePanelRef.current.children)
      if (targets.length) {
        animate(targets, {
          opacity: [0, 1],
          y: [24, 0],
          scale: [0.985, 1],
          delay: stagger(0.04),
          duration: 0.45,
          ease: 'outExpo',
        })
      }
    }
  }, [renderedView, transitionPhase])

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

  // Guarantee logged-in users NEVER see the public Home page (redirect to workspace)
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
      properties: {
        previous_view: previousView || null,
        current_view: view,
      },
    })
    previousViewRef.current = view
  }, [sessionId, view])

  function handleOnboardingCompleted(payload) {
    setSessionId(payload.session_id)
    setView(AUTHENTICATED_LANDING_VIEW)
  }

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

  function handleOpenGuidedInvesting(focusCard = 'overview') {
    setGuidedFocusCard(focusCard)
    openProtectedView('guided_investing')
  }

  function handleOpenGlobalTerminal() {
    openProtectedView('global_terminal')
  }

  function handleOpenNews() {
    openProtectedView('news')
  }

  function handleOpenProLab() {
    openProtectedView('pro_lab')
  }

  function handleOpenSimulationLab() {
    handleOpenProLab()
  }

  function handleOpenBacktestStudio(context = {}) {
    setProLabBacktestContext((current) => ({
      selectedBlueprintId: context.selectedBlueprintId || current.selectedBlueprintId || '',
      workspace: context.workspace || current.workspace || null,
      accessToken: context.accessToken || current.accessToken || '',
    }))
    setView('backtest_studio')
  }

  function handleAuthSuccess(payload) {
    setSessionId(payload.session_id)
    setView(pendingPostAuthView || AUTHENTICATED_LANDING_VIEW)
    setPendingPostAuthView('')
  }

  function handleAuthSwitchMode(newMode) {
    setView(newMode === 'register' ? 'auth_register' : 'auth_login')
  }

  function handleLogout() {
    window.localStorage.removeItem('public-beta.session_id')
    window.localStorage.removeItem('public-beta.user_profile')
    window.localStorage.removeItem('public-beta.view')
    setSessionId('')
    setPendingPostAuthView('')
    setView('home', { replace: true })
  }

  let content = null

  if (renderedView === 'learning') {
    content = (
      <LearningHomePage
        sessionId={sessionId}
        onBack={() => setView('home')}
      />
    )
  }

  if (renderedView === 'global_terminal') {
    content = (
      <MarketPortfolioPage
        sessionId={sessionId}
        onBack={() => setView('home')}
        onOpenProLab={handleOpenProLab}
        onOpenNews={handleOpenNews}
        onOpenLogin={() => setView('auth_login')}
      />
    )
  }

  if (renderedView === 'news') {
    content = (
      <NewsPage
        sessionId={sessionId}
        onBack={() => setView('home')}
        onOpenGlobalTerminal={handleOpenGlobalTerminal}
      />
    )
  }

  if (renderedView === 'news_economic_calendar') {
    content = (
      <NewsEconCalendarPage onBackToNews={handleOpenNews} />
    )
  }

  if (renderedView === 'guided_investing') {
    content = (
      <GuidedInvestingPage
        sessionId={sessionId}
        initialFocusCard={guidedFocusCard}
        onBack={() => setView('home')}
        onOpenLearning={() => setView('learning')}
        onOpenProLab={handleOpenProLab}
      />
    )
  }

  if (renderedView === 'pro_lab') {
    content = (
      <ProLabPage
        sessionId={sessionId}
        onBack={() => setView('home')}
        onOpenBacktestStudio={handleOpenBacktestStudio}
      />
    )
  }

  if (renderedView === 'backtest_studio') {
    content = (
      <ProLabBacktestStudioPage
        sessionId={sessionId}
        selectedBlueprintId={proLabBacktestContext.selectedBlueprintId}
        workspace={proLabBacktestContext.workspace}
        accessToken={proLabBacktestContext.accessToken}
        onBack={() => setView('pro_lab')}
        onOpenBlueprints={() => setView('pro_lab')}
      />
    )
  }

  if (renderedView === 'onboarding') {
    content = (
      <OnboardingPage
        onCompleted={handleOnboardingCompleted}
        onOpenHome={() => setView('home')}
        onOpenGlobalTerminal={handleOpenGlobalTerminal}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenProLab={handleOpenProLab}
      />
    )
  }

  if (renderedView === 'auth_login') {
    content = (
      <AuthPage
        mode="login"
        onAuthSuccess={handleAuthSuccess}
        onNavigateHome={() => setView('home')}
        onSwitchMode={handleAuthSwitchMode}
      />
    )
  }

  if (renderedView === 'auth_register') {
    content = (
      <AuthPage
        mode="register"
        onAuthSuccess={handleAuthSuccess}
        onNavigateHome={() => setView('home')}
        onSwitchMode={handleAuthSwitchMode}
      />
    )
  }
  if (!content) {
    content = (
      <HomePage
        sessionId={sessionId}
        onOpenLearning={() => openProtectedView('learning')}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenGlobalTerminal={handleOpenGlobalTerminal}
        onOpenNews={handleOpenNews}
        onOpenProLab={handleOpenProLab}
        onOpenOnboarding={() => openProtectedView('onboarding')}
      />
    )
  }

  const isEconCalendarEmbed =
    view === 'news_economic_calendar' &&
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('embed') === '1'

  if (isEconCalendarEmbed) {
    return (
      <div className="app-shell app-shell--embed-calendar app-shell--public app-shell--transition-entered">
        <main className="app-shell__embed-calendar-main">
          <NewsEconCalendarPage embed onBackToNews={handleOpenNews} />
        </main>
      </div>
    )
  }

  const tone = (renderedView === 'pro_lab' || renderedView === 'backtest_studio') ? 'pro' : 'public'
  const themeAttr = !isPublicView(renderedView) ? 'dark' : 'light'

  const connectedNavActions = {
    openHome: () => {
      if (sessionId) {
        setView(AUTHENTICATED_LANDING_VIEW)
      } else {
        setView('home')
      }
    },
    openLearning: () => openProtectedView('learning'),
    openSimulationLab: handleOpenSimulationLab,
    openGuidedInvesting: (payload) => {
      handleOpenGuidedInvesting(typeof payload === 'string' ? payload : 'overview')
    },
    openGlobalTerminal: handleOpenGlobalTerminal,
    openNews: handleOpenNews,
    openProLab: handleOpenProLab,
    openLogin: () => setView('auth_login'),
    openRegister: () => setView('auth_register'),
    openLogout: handleLogout,
  }

  const shellSkin = renderedView === 'news_economic_calendar' ? 'news' : renderedView

  return (
    <div className={`app-shell app-shell--${shellSkin.replaceAll('_', '-')} app-shell--${tone} app-shell--transition-${transitionPhase} ${themeAttr}`} data-theme={themeAttr}>
      <div className="app-shell__ambient app-shell__ambient--one" />
      <div className="app-shell__ambient app-shell__ambient--two" />
      <div className="app-shell__frame">
        <NavBar
          renderedView={renderedView}
          tone={tone}
          sessionId={sessionId}
          onNavigateHome={() => setView('home')}
          onOpenTerminal={handleOpenGlobalTerminal}
        />
        <main className="app-shell__content">
          <ConnectedWorkspaceNav currentView={renderedView} sessionId={sessionId} actions={connectedNavActions} showTabs={Boolean(sessionId)} />
          <AnimatePresence mode="wait">
            <motion.div
              key={renderedView}
              ref={surfacePanelRef}
              className="surface-panel"
              initial={{ opacity: 0, y: 16, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.99 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              data-transition-phase={transitionPhase}
            >
              {content}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

function normalizeView(view) {
  return DEPRECATED_VIEW_ALIASES[view] || view
}

function isPublicView(view) {
  return PUBLIC_VIEWS.has(normalizeView(view))
}
