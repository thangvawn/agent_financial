/**
 * Route prefetcher: triggers dynamic import() on hover
 * to cache page chunks before the user clicks, enabling 0ms navigation.
 */
const prefetchCache = new Set()

export function prefetchView(view) {
  if (!view || prefetchCache.has(view)) return
  prefetchCache.add(view)

  switch (view) {
    case 'news_social':
      import('../features/news/pages/SocialPage.jsx')
      break
    case 'global_terminal':
      import('../features/market-portfolio/pages/MarketPortfolioPage.jsx')
      break
    case 'news':
    case 'news_economic_calendar':
      import('../features/news/pages/NewsPage.jsx')
      break
    case 'learning':
      import('../features/learn-hub/pages/LearningHomePage.jsx')
      break
    case 'guided_investing':
      import('../features/bctc/pages/GuidedInvestingPage.jsx')
      break
    case 'pro_lab':
      import('../features/simulation-lab/pages/ProLabPage.jsx')
      break
    case 'home':
      import('../features/home/pages/HomePage.jsx')
      break
    case 'auth_login':
    case 'auth_register':
      import('../features/auth/pages/AuthPage.jsx')
      break
    default:
      break
  }
}
