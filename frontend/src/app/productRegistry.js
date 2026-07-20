/**
 * Single source of truth for Northstar product domains.
 * Keep route aliases for backward compatibility.
 */
export const PRODUCT_DOMAINS = [
  {
    id: 'home',
    label: 'Home',
    short: 'Giới thiệu tổng quan',
    view: 'home',
    routes: ['/', '/home', '/dashboard'],
    featurePath: 'features/home',
  },
  {
    id: 'market_portfolio',
    label: 'Market & Portfolio',
    mobileLabel: 'Thị trường',
    short: 'Bảng điện & danh mục',
    view: 'global_terminal',
    routes: ['/markets', '/market', '/portfolio', '/global-terminal'],
    featurePath: 'features/market-portfolio',
    navAction: 'openGlobalTerminal',
  },
  {
    id: 'learn_hub',
    label: 'Learn Hub',
    mobileLabel: 'Học',
    short: 'Video, sách & tài liệu',
    view: 'learning',
    routes: ['/learn', '/learning'],
    featurePath: 'features/learn-hub',
    navAction: 'openLearning',
  },
  {
    id: 'bctc',
    label: 'BCTC',
    mobileLabel: 'BCTC',
    short: 'Phân tích báo cáo TC',
    view: 'guided_investing',
    routes: ['/bctc', '/guided-investing'],
    featurePath: 'features/bctc',
    navAction: 'openGuidedInvesting',
  },
  {
    id: 'news',
    label: 'News',
    mobileLabel: 'Tin tức',
    short: 'Tin tức & sàng lọc',
    view: 'news',
    routes: ['/news', '/news-desk'],
    featurePath: 'features/news',
    navAction: 'openNews',
  },
  {
    id: 'simulation_lab',
    label: 'Simulation Lab',
    mobileLabel: 'Mô phỏng',
    short: 'Backtest & thực hành',
    view: 'pro_lab',
    routes: ['/simulation-lab', '/simulations', '/pro-lab'],
    featurePath: 'features/simulation-lab',
    navAction: 'openProLab',
  },
]

export const NAV_FLOW = PRODUCT_DOMAINS.filter((domain) => domain.navAction)
