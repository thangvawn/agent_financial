import { useFinancialWorkflow } from '../shared/context/FinancialWorkflowContext'
import { AccountContext } from '../shared/auth/accountContext'
import { verifySession, clearStoredSession, SESSION_INVALID_EVENT } from '../features/auth/services/sessionClient'
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { trackAnalyticsEvent } from '../shared/analytics/trackEvent'
import ConnectedWorkspaceNav from '../shared/navigation/ConnectedWorkspaceNav'
import NavBar from './NavBar'
import { logoutSession } from '../features/auth/services/sessionLifecycle'
import AppShellRoutes from './AppShellRoutes'
import { ThemeContext, useAppTheme } from '../shared/theme/appTheme'

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
  const appTheme = useAppTheme()
  const { resetWorkflow } = useFinancialWorkflow()
  const [internalView, setInternalView] = useState(() => normalizeView(initialView))
  const requestedView = normalizeView(controlledView || internalView)
  const [sessionId, setSessionId] = useState(() => readStoredSession())
  const [identity, setIdentity] = useState({ sessionId: '', accountId: '', error: '' })
  const [verifyNonce, setVerifyNonce] = useState(0)
  const [guidedFocusCard, setGuidedFocusCard] = useState('overview')
  const [learningFocus, setLearningFocus] = useState({ tab: 'courses', search: '' })
  const [proLabBacktestContext, setProLabBacktestContext] = useState({ selectedBlueprintId: '', workspace: null, accessToken: '' })
  const [pendingPostAuthView, setPendingPostAuthView] = useState(() => isPublicView(requestedView) ? '' : requestedView)
  const [logoutError, setLogoutError] = useState('')
  const previousViewRef = useRef('')
  const clearPrivateState = useCallback(() => {
    resetWorkflow()
    setProLabBacktestContext({ selectedBlueprintId: '', workspace: null, accessToken: '' })
  }, [resetWorkflow])
  const view = !sessionId && !isPublicView(requestedView) ? 'auth_login'
    : sessionId && requestedView === 'home' ? AUTHENTICATED_LANDING_VIEW : requestedView
  const [lastRoute, setLastRoute] = useState({ requestedView, sessionId })
  if (lastRoute.requestedView !== requestedView || lastRoute.sessionId !== sessionId) {
    setLastRoute({ requestedView, sessionId })
    if (!sessionId && !isPublicView(requestedView)) setPendingPostAuthView(requestedView)
  }

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    verifySession(sessionId).then(payload => {
      if (cancelled) return
      window.localStorage.setItem('public-beta.user_profile', JSON.stringify(payload.profile))
      setIdentity({sessionId, accountId:payload.profile.account_id, error:''})
    }).catch(error => {
      if (cancelled) return
      if (error.status === 401) { clearStoredSession(); clearPrivateState(); setSessionId(''); setIdentity({sessionId:'',accountId:'',error:''}) }
      else setIdentity({sessionId,accountId:'',error:error.message})
    })
    return () => { cancelled = true }
  }, [sessionId, verifyNonce, clearPrivateState])

  useEffect(() => {
    function invalid(event) {
      if (event.detail.sessionId !== sessionId) return
      clearStoredSession(); clearPrivateState(); setSessionId(''); setIdentity({sessionId:'',accountId:'',error:''})
    }
    function changed(event) {
      if (event.key === 'public-beta.session_id' || event.key === null) {
        clearPrivateState()
        setSessionId(readStoredSession())
      }
    }
    window.addEventListener(SESSION_INVALID_EVENT, invalid)
    window.addEventListener('storage', changed)
    return () => { window.removeEventListener(SESSION_INVALID_EVENT, invalid); window.removeEventListener('storage', changed) }
  }, [sessionId, clearPrivateState])

  useEffect(() => {
    if (sessionId) window.localStorage.setItem('public-beta.session_id', sessionId)
    window.localStorage.setItem('public-beta.view', view)
  }, [sessionId, view])

  useEffect(() => {
    if (requestedView !== view) onNavigate?.(view, { replace: true })
  }, [onNavigate, requestedView, view])

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
  const themeAttr = appTheme.theme
  const shellSkin = ['news_economic_calendar', 'news_social'].includes(view) ? 'news' : view

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
    openLogout: async () => {
      setLogoutError('')
      try {
        await logoutSession()
        clearPrivateState()
        setIdentity({sessionId:'',accountId:'',error:''})
        setSessionId('')
        setPendingPostAuthView('')
        setProLabBacktestContext({ selectedBlueprintId: '', workspace: null, accessToken: '' })
        setView('home', { replace: true })
      } catch (error) { setLogoutError(error.message) }
    },
  }

  const routeActions = {
    onOpenSocial: () => openProtectedView('news_social'),
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
      clearPrivateState()
      setIdentity({sessionId:payload.session_id,accountId:payload.profile.account_id,error:''})
      setSessionId(payload.session_id)
      setView(pendingPostAuthView || AUTHENTICATED_LANDING_VIEW)
      setPendingPostAuthView('')
    },
    onAuthSwitchMode: (mode) => setView(mode === 'register' ? 'auth_register' : 'auth_login'),
    onOnboardingCompleted: () => {
      setView(AUTHENTICATED_LANDING_VIEW)
    },
  }

  return (
    <ThemeContext.Provider value={appTheme}>
    <div className={`app-shell app-shell--${shellSkin.replaceAll('_', '-')} app-shell--${tone} ${themeAttr}`} data-theme={themeAttr}>
      <div className="app-shell__ambient app-shell__ambient--one" />
      <div className="app-shell__ambient app-shell__ambient--two" />
      <div className="app-shell__frame">
        <NavBar renderedView={view} tone={tone} sessionId={sessionId} onNavigateHome={() => setView('home')} onOpenTerminal={() => openProtectedView('global_terminal')} />
        <main className="app-shell__content">
          {logoutError && <p role="alert">{logoutError}</p>}
          <ConnectedWorkspaceNav currentView={view} sessionId={sessionId} actions={connectedNavActions} showTabs={Boolean(sessionId)} />
          <motion.div
            key={view}
            className="surface-panel"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
          >
            {sessionId && !isPublicView(view) && (identity.sessionId !== sessionId || !identity.accountId) ? (
              <div role="status">{identity.error ? <><p role="alert">{identity.error}</p><button onClick={() => setVerifyNonce(n => n+1)}>Thử xác minh lại</button></> : 'Đang xác minh phiên…'}</div>
            ) : <AccountContext.Provider key={sessionId ? identity.accountId : 'guest'} value={sessionId ? identity.accountId : ''}>
            <AppShellRoutes
              renderedView={view}
              sessionId={sessionId}
              learningFocus={learningFocus}
              guidedFocusCard={guidedFocusCard}
              proLabBacktestContext={proLabBacktestContext}
              actions={routeActions}
            />
            </AccountContext.Provider>}
          </motion.div>
        </main>
      </div>
    </div>
    </ThemeContext.Provider>
  )
}

function normalizeView(view) {
  return DEPRECATED_VIEW_ALIASES[view] || view
}

function isPublicView(view) {
  return PUBLIC_VIEWS.has(normalizeView(view))
}
