export const DOMAIN_ROUTES = {
  '/': 'home',
  '/home': 'home',
  '/dashboard': 'home',
  '/onboarding': 'onboarding',
  '/learn': 'learning',
  '/learning': 'learning',
  '/financial-statement-simulator': 'financial_statement_simulator',
  '/assignments': 'guided_investing',
  '/global-terminal': 'global_terminal',
  '/markets': 'global_terminal',
  '/simulation-lab': 'global_terminal',
  '/simulations': 'global_terminal',
  '/news': 'news',
  '/news/economic-calendar': 'news_economic_calendar',
  '/news-desk': 'news',
  '/guided-investing': 'guided_investing',
  '/insights': 'insights',
  '/community': 'community',
  '/pro-lab': 'pro_lab',
  '/backtest-studio': 'backtest_studio',
  '/admin': 'content_ops_admin',
  '/admin/content-ops': 'content_ops_admin',
  '/admin/community': 'community_moderation',
  '/admin/pro-lab': 'pro_lab_admin',
  '/admin/trust-safety': 'trust_safety_admin',
  '/admin/analytics': 'analytics_admin',
  '/login': 'auth_login',
  '/register': 'auth_register',
  '/auth': 'auth_login',
}

export const VIEW_PATHS = Object.fromEntries(
  Object.entries(DOMAIN_ROUTES)
    .filter(([path]) => path !== '/dashboard')
    .reduce((entries, [path, view]) => {
      if (!entries.some(([, existingView]) => existingView === view)) entries.push([path, view])
      return entries
    }, [])
    .map(([path, view]) => [view, path]),
)

export function resolveDomainRoute(pathname = '/') {
  const normalizedPath = normalizeRoutePath(pathname)
  return DOMAIN_ROUTES[normalizedPath] || 'home'
}

export function resolvePathForView(view = 'home') {
  return withBasePath(VIEW_PATHS[view] || '/home')
}

function normalizeRoutePath(pathname = '/') {
  const base = import.meta.env.BASE_URL?.replace(/\/$/, '') || ''
  if (base && pathname.startsWith(`${base}/`)) return pathname.slice(base.length) || '/'
  if (base && pathname === base) return '/'
  return pathname
}

function withBasePath(path = '/') {
  const base = import.meta.env.BASE_URL?.replace(/\/$/, '') || ''
  if (!base || base === '/') return path
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}
