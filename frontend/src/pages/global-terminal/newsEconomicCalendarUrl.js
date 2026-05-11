/**
 * SPA deep-link at the **app root** (same as `/news`), not under `/dashboard-static/`.
 * StaticFiles has no HTML fallback for nested paths; FastAPI serves `index.html` for these routes.
 */
export function getNewsEconomicCalendarUrl() {
  if (typeof window === 'undefined') return '/news/economic-calendar'
  return `${window.location.origin}/news/economic-calendar`
}

/** Chỉ khối lịch Finnhub — dùng trong iframe overlay (`?embed=1`, AppShell tối giản). */
export function getNewsEconomicCalendarEmbedUrl() {
  if (typeof window === 'undefined') return '/news/economic-calendar?embed=1'
  const u = new URL('/news/economic-calendar', window.location.origin)
  u.searchParams.set('embed', '1')
  return u.href
}
