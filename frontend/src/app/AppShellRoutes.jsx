import { lazy, Suspense } from 'react'
import PageSkeleton from './PageSkeleton'

// Code-split pages on demand to reduce initial bundle from 1.7MB down to ~200kB
const AuthPage = lazy(() => import('../features/auth/pages/AuthPage.jsx'))
const HomePage = lazy(() => import('../features/home/pages/HomePage.jsx'))
const OnboardingPage = lazy(() => import('../features/home/pages/OnboardingPage.jsx'))
const MarketPortfolioPage = lazy(() => import('../features/market-portfolio/pages/MarketPortfolioPage.jsx'))
const NewsPage = lazy(() => import('../features/news/pages/NewsPage.jsx'))
const SocialPage = lazy(() => import('../features/news/pages/SocialPage.jsx'))
const NewsEconCalendarPage = lazy(() => import('../features/news/pages/NewsEconCalendarPage.jsx'))
const GuidedInvestingPage = lazy(() => import('../features/bctc/pages/GuidedInvestingPage.jsx'))
const LearningHomePage = lazy(() => import('../features/learn-hub/pages/LearningHomePage.jsx'))
const ProLabPage = lazy(() => import('../features/simulation-lab/pages/ProLabPage.jsx'))
const ProLabBacktestStudioPage = lazy(() => import('../features/simulation-lab/pages/ProLabBacktestStudioPage.jsx'))

export default function AppShellRoutes({
  renderedView,
  sessionId,
  learningFocus,
  guidedFocusCard,
  proLabBacktestContext,
  actions,
}) {
  let content = null

  if (renderedView === 'learning') {
    content = (
      <LearningHomePage
        key={`learning-${learningFocus.tab}-${learningFocus.search}`}
        sessionId={sessionId}
        onBack={actions.onBackHome}
        initialSubTab={learningFocus.tab}
        initialSearch={learningFocus.search}
      />
    )
  } else if (renderedView === 'global_terminal') {
    content = (
      <MarketPortfolioPage
        sessionId={sessionId}
        onBack={actions.onBackHome}
        onOpenProLab={actions.onOpenProLab}
        onOpenNews={actions.onOpenNews}
        onOpenLogin={actions.onOpenLogin}
      />
    )
  } else if (renderedView === 'news') {
    content = (
      <NewsPage
        onOpenSocial={actions.onOpenSocial}
        sessionId={sessionId}
        onBack={actions.onBackHome}
        onOpenGlobalTerminal={actions.onOpenGlobalTerminal}
      />
    )
  } else if (renderedView === 'news_social') {
    content = <SocialPage sessionId={sessionId} onOpenNews={actions.onOpenNews} />
  } else if (renderedView === 'news_economic_calendar') {
    content = <NewsEconCalendarPage onBackToNews={actions.onOpenNews} />
  } else if (renderedView === 'guided_investing') {
    content = (
      <GuidedInvestingPage
        sessionId={sessionId}
        initialFocusCard={guidedFocusCard}
        onBack={actions.onBackHome}
        onOpenLearning={actions.onOpenLearning}
        onOpenProLab={actions.onOpenProLab}
      />
    )
  } else if (renderedView === 'pro_lab') {
    content = (
      <ProLabPage
        sessionId={sessionId}
        onBack={actions.onBackHome}
        onOpenBacktestStudio={actions.onOpenBacktestStudio}
      />
    )
  } else if (renderedView === 'backtest_studio') {
    content = (
      <ProLabBacktestStudioPage
        sessionId={sessionId}
        selectedBlueprintId={proLabBacktestContext.selectedBlueprintId}
        workspace={proLabBacktestContext.workspace}
        accessToken={proLabBacktestContext.accessToken}
        onBack={actions.onBackProLab}
        onOpenBlueprints={actions.onBackProLab}
      />
    )
  } else if (renderedView === 'onboarding') {
    content = (
      <OnboardingPage
        onCompleted={actions.onOnboardingCompleted}
        onOpenHome={actions.onBackHome}
        onOpenGlobalTerminal={actions.onOpenGlobalTerminal}
        onOpenGuidedInvesting={actions.onOpenGuidedInvesting}
        onOpenProLab={actions.onOpenProLab}
      />
    )
  } else if (renderedView === 'auth_login' || renderedView === 'auth_register') {
    content = (
      <AuthPage
        mode={renderedView === 'auth_register' ? 'register' : 'login'}
        onAuthSuccess={actions.onAuthSuccess}
        onNavigateHome={actions.onBackHome}
        onSwitchMode={actions.onAuthSwitchMode}
      />
    )
  } else {
    content = (
      <HomePage
        sessionId={sessionId}
        onOpenLearning={actions.onOpenLearning}
        onOpenGuidedInvesting={actions.onOpenGuidedInvesting}
        onOpenGlobalTerminal={actions.onOpenGlobalTerminal}
        onOpenNews={actions.onOpenNews}
        onOpenProLab={actions.onOpenProLab}
        onOpenOnboarding={actions.onOpenOnboarding}
      />
    )
  }

  return (
    <Suspense fallback={<PageSkeleton />}>
      {content}
    </Suspense>
  )
}
