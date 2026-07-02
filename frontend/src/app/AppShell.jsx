import { useEffect, useRef, useState } from 'react'
import { animate, stagger } from 'animejs'

import {
  AnalyticsAdminPage,
  AuthPage,
  CommunityModerationPage,
  CommunityPage,
  ContentOpsAdminPage,
  EducationPlatformPage,
  GlobalTerminalPage,
  GuidedInvestingPage,
  HomePage,
  InsightsPage,
  LearningHomePage,
  NewsEconCalendarPage,
  NewsPage,
  OnboardingPage,
  ProLabAdminPage,
  ProLabBacktestStudioPage,
  ProLabPage,
  TrustSafetyAdminPage,
} from '../pages'
import FloatingAssistant from '../shared/assistant/FloatingAssistant'
import { trackAnalyticsEvent } from '../shared/analytics/trackEvent'
import ConnectedWorkspaceNav from '../shared/navigation/ConnectedWorkspaceNav'
import NavBar from './NavBar'

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

const PAGE_TRANSITION_MS = 200
const AUTHENTICATED_LANDING_VIEW = 'global_terminal'
const DEPRECATED_VIEW_ALIASES = {
  simulation_lab: 'global_terminal',
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
  const [homeRefreshKey, setHomeRefreshKey] = useState(0)
  const [guidedFocusCard, setGuidedFocusCard] = useState('overview')
  const [proLabBacktestContext, setProLabBacktestContext] = useState({ selectedBlueprintId: '', workspace: null, accessToken: '' })
  const [communityFocusSpace, setCommunityFocusSpace] = useState('')
  const [learningFocusView, setLearningFocusView] = useState('lesson')
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
    setHomeRefreshKey((current) => current + 1)
    setView('home')
  }

  function handleSessionInvalid() {
    window.localStorage.removeItem('public-beta.session_id')
    setSessionId('')
    setHomeRefreshKey((current) => current + 1)
    setView('home', { replace: true })
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

  function handleOpenInsights() {
    openProtectedView('insights')
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
    handleOpenGlobalTerminal()
  }

  function handleOpenAssignments() {
    openProtectedView('assignments')
  }

  function handleOpenProLabAdmin() {
    setView('pro_lab_admin')
  }

  function handleOpenBacktestStudio(context = {}) {
    setProLabBacktestContext({
      selectedBlueprintId: context.selectedBlueprintId || '',
      workspace: context.workspace || null,
      accessToken: context.accessToken || '',
    })
    setView('backtest_studio')
  }

  function handleOpenTrustSafetyAdmin() {
    setView('trust_safety_admin')
  }

  function handleOpenAnalyticsAdmin() {
    setView('analytics_admin')
  }

  function handleOpenCommunity(spaceId = '') {
    setCommunityFocusSpace(spaceId)
    openProtectedView('community')
  }

  function handleOpenCommunityModeration() {
    setView('community_moderation')
  }

  function handleAuthSuccess(payload) {
    setSessionId(payload.session_id)
    setHomeRefreshKey((current) => current + 1)
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
    setHomeRefreshKey((current) => current + 1)
    setView('home', { replace: true })
  }

  let content = null

  if (renderedView === 'learning') {
    content = (
      <LearningHomePage
        sessionId={sessionId}
        initialFocusView={learningFocusView}
        onBack={() => setView('home')}
        onOpenCommunity={handleOpenCommunity}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenInsights={handleOpenInsights}
        onOpenAdmin={() => setView('content_ops_admin')}
      />
    )
  }

  if (renderedView === 'content_ops_admin') {
    content = <ContentOpsAdminPage onBack={() => setView('learning')} />
  }

  if (['financial_statement_simulator', 'assignments'].includes(renderedView)) {
    content = (
      <EducationPlatformPage
        surface={renderedView}
        onBack={() => setView('home')}
      />
    )
  }

  if (renderedView === 'global_terminal') {
    content = (
      <GlobalTerminalPage
        onBack={() => setView('home')}
        onOpenInsights={handleOpenInsights}
        onOpenProLab={handleOpenProLab}
        onOpenNews={handleOpenNews}
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

  if (renderedView === 'community') {
    content = (
      <CommunityPage
        sessionId={sessionId}
        initialSpaceId={communityFocusSpace}
        onBack={() => setView('home')}
        onOpenLearning={() => setView('learning')}
        onOpenModeration={handleOpenCommunityModeration}
      />
    )
  }

  if (renderedView === 'community_moderation') {
    content = <CommunityModerationPage onBack={() => setView('community')} />
  }

  if (renderedView === 'guided_investing') {
    content = (
      <GuidedInvestingPage
        sessionId={sessionId}
        initialFocusCard={guidedFocusCard}
        onBack={() => setView('home')}
        onOpenInsights={handleOpenInsights}
        onOpenLearning={() => setView('learning')}
        onOpenCommunity={handleOpenCommunity}
        onOpenProLab={handleOpenProLab}
      />
    )
  }

  if (renderedView === 'insights') {
    content = (
      <InsightsPage
        sessionId={sessionId}
        onBack={() => setView('home')}
        onOpenLearning={() => setView('learning')}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenProLab={handleOpenProLab}
      />
    )
  }

  if (renderedView === 'pro_lab') {
    content = (
      <ProLabPage
        sessionId={sessionId}
        onBack={() => setView('home')}
        onOpenAdmin={handleOpenProLabAdmin}
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

  if (renderedView === 'pro_lab_admin') {
    content = <ProLabAdminPage onBack={() => setView('pro_lab')} onOpenTrustSafety={handleOpenTrustSafetyAdmin} onOpenAnalytics={handleOpenAnalyticsAdmin} />
  }

  if (renderedView === 'trust_safety_admin') {
    content = <TrustSafetyAdminPage onBack={() => setView('pro_lab_admin')} />
  }

  if (renderedView === 'analytics_admin') {
    content = <AnalyticsAdminPage onBack={() => setView('pro_lab_admin')} />
  }

  if (renderedView === 'onboarding') {
    content = (
      <OnboardingPage
        onCompleted={handleOnboardingCompleted}
        onOpenHome={() => setView('home')}
        onOpenGlobalTerminal={handleOpenGlobalTerminal}
        onOpenInsights={handleOpenInsights}
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
        refreshKey={homeRefreshKey}
        onOpenLearning={() => openProtectedView('learning')}
        onOpenSimulationLab={handleOpenSimulationLab}
        onOpenAssignments={handleOpenAssignments}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenInsights={handleOpenInsights}
        onOpenGlobalTerminal={handleOpenGlobalTerminal}
        onOpenProLab={handleOpenProLab}
        onOpenCommunity={handleOpenCommunity}
        onOpenOnboarding={() => openProtectedView('onboarding')}
        onSessionInvalid={handleSessionInvalid}
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

  const tone = renderedView.includes('admin') ? 'operator' : (renderedView === 'pro_lab' || renderedView === 'backtest_studio') ? 'pro' : 'public'
  const themeAttr = !isPublicView(renderedView) ? 'dark' : 'light'
  const isAuthView = renderedView === 'auth_login' || renderedView === 'auth_register'
  const hideAssistant = isAuthView || ['backtest_studio', 'global_terminal', 'news', 'news_economic_calendar'].includes(renderedView)
  const connectedNavActions = {
    openHome: () => setView('home'),
    openLearning: (payload) => {
      setLearningFocusView(typeof payload === 'string' ? payload : 'lesson')
      openProtectedView('learning')
    },
    openSimulationLab: handleOpenSimulationLab,
    openAssignments: handleOpenAssignments,
    openGuidedInvesting: (payload) => {
      handleOpenGuidedInvesting(typeof payload === 'string' ? payload : 'overview')
    },
    openInsights: handleOpenInsights,
    openGlobalTerminal: handleOpenGlobalTerminal,
    openNews: handleOpenNews,
    openCommunity: handleOpenCommunity,
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
          <div ref={surfacePanelRef} className="surface-panel" key={renderedView} data-transition-phase={transitionPhase}>
            {content}
          </div>
        </main>
        {!hideAssistant ? <FloatingAssistant sessionId={sessionId} surface={renderedView} surfaceLabel={SURFACE_LABELS[renderedView] || 'Workspace'} /> : null}
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
