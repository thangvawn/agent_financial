const QUEUE = []
let flushTimer = null

function buildEvent(payload) {
  return {
    event_name: payload.event_name,
    event_category: payload.event_category || 'product',
    schema_version: 1,
    timestamp: new Date().toISOString(),
    module: payload.module,
    surface: payload.surface,
    user_id: payload.user_id || undefined,
    session_id: payload.session_id || undefined,
    route: payload.route || window.location.pathname,
    source_surface: payload.source_surface || undefined,
    target_surface: payload.target_surface || undefined,
    properties: payload.properties || {},
  }
}

async function flushQueue() {
  flushTimer = null
  if (!QUEUE.length) return
  const events = QUEUE.splice(0, QUEUE.length)
  const body = JSON.stringify({ events })
  try {
    if (navigator.sendBeacon && body.length < 60_000) {
      const blob = new Blob([body], { type: 'application/json' })
      navigator.sendBeacon('/api/v1/public/analytics/events', blob)
      return
    }
    await fetch('/api/v1/public/analytics/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    })
  } catch {
    // analytics must stay best-effort
  }
}

export function trackAnalyticsEvent(payload) {
  if (!payload?.event_name || !payload?.module || !payload?.surface) return
  QUEUE.push(buildEvent(payload))
  if (QUEUE.length >= 10) {
    void flushQueue()
    return
  }
  if (!flushTimer) {
    flushTimer = window.setTimeout(() => {
      void flushQueue()
    }, 500)
  }
}

window.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    void flushQueue()
  }
})

