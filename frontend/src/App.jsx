import { useEffect, useState } from 'react'

import AppShell from './app/AppShell.jsx'
import { resolveDomainRoute, resolvePathForView } from './app/domainRoutes'
import { FinancialWorkflowProvider } from './shared/context/FinancialWorkflowProvider.jsx'
import TickerActionPopover from './shared/components/TickerActionPopover.jsx'
import './shared/styles/fintech-typography.css'

export default function App() {
  const [view, setView] = useState(() => resolveCurrentView())

  useEffect(() => {
    function handlePopState() {
      setView(resolveCurrentView())
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  function navigate(nextView, options = {}) {
    const nextPath = resolvePathForView(nextView)
    setView(nextView)

    if (typeof window === 'undefined') return
    if (window.location.pathname === nextPath) return

    const method = options.replace ? 'replaceState' : 'pushState'
    window.history[method]({ view: nextView }, '', nextPath)
  }

  return (
    <FinancialWorkflowProvider onNavigateView={navigate}>
      <AppShell view={view} onNavigate={navigate} />
      <TickerActionPopover />
    </FinancialWorkflowProvider>
  )
}

function resolveCurrentView() {
  if (typeof window === 'undefined') return 'home'
  return resolveDomainRoute(window.location.pathname)
}

