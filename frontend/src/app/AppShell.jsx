import { useEffect, useRef, useState } from 'react'

import {
  AnalyticsAdminPage,
  AuthPage,
  CommunityModerationPage,
  CommunityPage,
  ContentOpsAdminPage,
  FinancialHealthPage,
  GoalsPage,
  GlobalTerminalPage,
  GuidedInvestingPage,
  HomePage,
  InsightsPage,
  LearningHomePage,
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

const SURFACE_LABELS = {
  onboarding: 'Onboarding',
  home: 'Home',
  financial_health: 'Financial Health',
  learning: 'Learn Hub',
  content_ops_admin: 'Content Ops',
  goals: 'Goals',
  global_terminal: 'Global Terminal',
  news: 'News Desk',
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

const PAGE_TRANSITION_MS = 180

export default function AppShell({ initialView = 'home', view: controlledView, onNavigate }) {
  const [internalView, setInternalView] = useState(() => initialView)
  const view = controlledView || internalView
  const [renderedView, setRenderedView] = useState(() => view)
  const [transitionPhase, setTransitionPhase] = useState('entered')
  const [sessionId, setSessionId] = useState('')
  const [homeRefreshKey, setHomeRefreshKey] = useState(0)
  const [focusedGoalId, setFocusedGoalId] = useState('')
  const [guidedFocusCard, setGuidedFocusCard] = useState('market_context')
  const [communityFocusSpace, setCommunityFocusSpace] = useState('')
  const previousViewRef = useRef('')

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
    const savedSessionId = window.localStorage.getItem('public-beta.session_id') || ''
    const savedView = window.localStorage.getItem('public-beta.view') || ''
    if (savedSessionId) {
      const locationView = initialView
      setSessionId(savedSessionId)
      if (!controlledView) {
        setView(savedView === 'learning_admin' ? locationView : (savedView || locationView))
      }
    }
  }, [controlledView, initialView])

  useEffect(() => {
    if (sessionId) window.localStorage.setItem('public-beta.session_id', sessionId)
    window.localStorage.setItem('public-beta.view', view)
  }, [sessionId, view])

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
    if (onNavigate) {
      onNavigate(nextView, options)
      return
    }
    setInternalView(nextView)
  }

  function handleFinancialHealthCompleted() {
    setHomeRefreshKey((current) => current + 1)
  }

  function handleGoalCompleted() {
    setHomeRefreshKey((current) => current + 1)
  }

  function handleOpenGoals(goalId = '') {
    setFocusedGoalId(goalId)
    setView('goals')
  }

  function handleOpenGuidedInvesting(focusCard = 'market_context') {
    setGuidedFocusCard(focusCard)
    setView('guided_investing')
  }

  function handleOpenInsights() {
    setView('insights')
  }

  function handleOpenGlobalTerminal() {
    setView('global_terminal')
  }

  function handleOpenNews() {
    setView('news')
  }

  function handleOpenProLab() {
    setView('pro_lab')
  }

  function handleOpenProLabAdmin() {
    setView('pro_lab_admin')
  }

  function handleOpenBacktestStudio() {
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
    setView('community')
  }

  function handleOpenCommunityModeration() {
    setView('community_moderation')
  }

  function handleAuthSuccess(payload) {
    setSessionId(payload.session_id)
    setHomeRefreshKey((current) => current + 1)
    setView('home')
  }

  function handleAuthSwitchMode(newMode) {
    setView(newMode === 'register' ? 'auth_register' : 'auth_login')
  }

  let content = null

  if (renderedView === 'financial_health') {
    content = (
      <FinancialHealthPage
        sessionId={sessionId}
        onCompleted={handleFinancialHealthCompleted}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onBack={() => setView('home')}
      />
    )
  }

  if (renderedView === 'learning') {
    content = (
      <LearningHomePage
        sessionId={sessionId}
        onBack={() => setView('home')}
        onOpenCommunity={handleOpenCommunity}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenFinancialHealth={() => setView('financial_health')}
        onOpenGoals={handleOpenGoals}
        onOpenInsights={handleOpenInsights}
        onOpenAdmin={() => setView('content_ops_admin')}
      />
    )
  }

  if (renderedView === 'content_ops_admin') {
    content = <ContentOpsAdminPage onBack={() => setView('learning')} />
  }

  if (renderedView === 'goals') {
    content = (
      <GoalsPage
        sessionId={sessionId}
        initialGoalId={focusedGoalId}
        onBack={() => setView('home')}
        onOpenCommunity={handleOpenCommunity}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onCompleted={handleGoalCompleted}
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

  if (renderedView === 'community') {
    content = (
      <CommunityPage
        sessionId={sessionId}
        initialSpaceId={communityFocusSpace}
        onBack={() => setView('home')}
        onOpenLearning={() => setView('learning')}
        onOpenGoals={handleOpenGoals}
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
        selectedBlueprintId=""
        workspace={null}
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
        onOpenFinancialHealth={() => setView('financial_health')}
        onOpenLearning={() => setView('learning')}
        onOpenGoals={handleOpenGoals}
        onOpenGuidedInvesting={handleOpenGuidedInvesting}
        onOpenInsights={handleOpenInsights}
        onOpenGlobalTerminal={handleOpenGlobalTerminal}
        onOpenProLab={handleOpenProLab}
        onOpenCommunity={handleOpenCommunity}
        onOpenOnboarding={() => setView('onboarding')}
        onSessionInvalid={handleSessionInvalid}
      />
    )
  }

  const tone = renderedView.includes('admin') ? 'operator' : (renderedView === 'pro_lab' || renderedView === 'backtest_studio') ? 'pro' : 'public'
  const isAuthView = renderedView === 'auth_login' || renderedView === 'auth_register'
  const hideAssistant = isAuthView || ['backtest_studio', 'global_terminal', 'news'].includes(renderedView)
  const connectedNavActions = {
    openHome: () => setView('home'),
    openFinancialHealth: () => setView('financial_health'),
    openLearning: () => setView('learning'),
    openGoals: handleOpenGoals,
    openGuidedInvesting: handleOpenGuidedInvesting,
    openInsights: handleOpenInsights,
    openGlobalTerminal: handleOpenGlobalTerminal,
    openNews: handleOpenNews,
    openCommunity: handleOpenCommunity,
    openProLab: handleOpenProLab,
    openLogin: () => setView('auth_login'),
  }

  return (
    <div className={`app-shell app-shell--${renderedView.replaceAll('_', '-')} app-shell--${tone} app-shell--transition-${transitionPhase}`}>
      <div className="app-shell__ambient app-shell__ambient--one" />
      <div className="app-shell__ambient app-shell__ambient--two" />
      <div className="app-shell__frame">
        <header className="app-shell__masthead">
          <div>
            <p className="app-shell__brand">North Star Public</p>
            <p className="app-shell__surface">{SURFACE_LABELS[renderedView] || 'Workspace'}</p>
          </div>
          <div className="app-shell__masthead-actions">
            <span className={`app-shell__badge app-shell__badge--${tone}`}>
              {tone === 'operator' ? 'Operator Surface' : tone === 'pro' ? 'Research Surface' : 'Retail Surface'}
            </span>
            {sessionId && renderedView !== 'home' && renderedView !== 'onboarding' ? (
              <button type="button" className="button-ghost" onClick={() => setView('home')}>
                Về Home
              </button>
            ) : null}
          </div>
        </header>
        <main className="app-shell__content">
          <ConnectedWorkspaceNav currentView={renderedView} sessionId={sessionId} actions={connectedNavActions} />
          <div className="surface-panel" key={renderedView} data-transition-phase={transitionPhase}>
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
