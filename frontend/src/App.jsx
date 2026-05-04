import { useEffect, useState } from 'react'

import AppShell from './app/AppShell.jsx'
import { resolveDomainRoute, resolvePathForView } from './app/domainRoutes'

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

  return <AppShell view={view} onNavigate={navigate} />
}

function resolveCurrentView() {
  if (typeof window === 'undefined') return 'home'
  return resolveDomainRoute(window.location.pathname)
}

