/**
 * Thematic Folders taxonomy and data normalizer for Books & Research Papers.
 */

export const DOCUMENT_TYPES = [
  { id: 'all', label: 'Tất cả tài liệu', icon: 'Library' },
  { id: 'book', label: 'Sách & Giáo trình', icon: 'BookOpen' },
  { id: 'paper', label: 'Paper Nghiên cứu', icon: 'FileText' },
]

export const DOCUMENT_FOLDERS = [
  {
    id: 'all',
    label: 'Tất cả chủ đề',
    icon: 'Folder',
    badgeColor: 'neutral',
    description: 'Toàn bộ sách và công trình nghiên cứu',
    topics: [],
  },
  {
    id: 'macro_crisis',
    label: 'Vĩ mô & Khủng hoảng',
    icon: 'Globe',
    badgeColor: 'amber',
    description: 'Chu kỳ kinh tế, chính sách tiền tệ, nợ và khủng hoảng',
    topics: ['macroeconomics', 'inflation'],
    keywords: ['vĩ mô', 'macro', 'khủng hoảng', 'crisis', 'tiền tệ', 'nợ', 'cpi', 'lạm phát'],
  },
  {
    id: 'bctc_valuation',
    label: 'BCTC & Định giá',
    icon: 'BarChart3',
    badgeColor: 'blue',
    description: 'Báo cáo tài chính, chiết khấu DCF, bội số định giá',
    topics: ['financial_statements', 'valuation'],
    keywords: ['bctc', 'định giá', 'valuation', 'financial statement', 'dcf', 'báo cáo tài chính'],
  },
  {
    id: 'stocks_investing',
    label: 'Cổ phiếu & Đầu tư Giá trị',
    icon: 'TrendingUp',
    badgeColor: 'emerald',
    description: 'Chiến lược đầu tư, cổ phiếu tăng trưởng, TTCK Việt Nam',
    topics: ['stocks', 'vietnam_market'],
    keywords: ['cổ phiếu', 'chứng khoán', 'stock', 'đầu tư', 'invest', 'buffett', 'graham', 'lynch'],
  },
  {
    id: 'quant_risk',
    label: 'Định lượng & Rủi ro',
    icon: 'Cpu',
    badgeColor: 'purple',
    description: 'Factor investing, mô hình toán, tối ưu danh mục và rủi ro',
    topics: ['quantitative_finance', 'risk_management', 'portfolio_theory'],
    keywords: ['định lượng', 'quant', 'quanta', 'dsl', 'risk', 'rủi ro', 'portfolio', 'markowitz', 'factor', 'wasserstein'],
  },
  {
    id: 'technical_trading',
    label: 'PTKT & Giao dịch',
    icon: 'Activity',
    badgeColor: 'cyan',
    description: 'Hành động giá, nến khối lượng VPA/Wyckoff, hệ thống giao dịch',
    topics: ['technical_analysis'],
    keywords: ['kỹ thuật', 'technical', 'giao dịch', 'trading', 'vpa', 'livermore', 'wyckoff', 'nến'],
  },
  {
    id: 'bonds_debt',
    label: 'Trái phiếu & Lãi suất',
    icon: 'Landmark',
    badgeColor: 'indigo',
    description: 'Thị trường nợ, đường cong lợi suất và chính sách lãi suất',
    topics: ['bonds', 'banking_products', 'time_value_of_money'],
    keywords: ['trái phiếu', 'bond', 'lãi suất', 'yield', 'yield curve', 'ngân hàng'],
  },
  {
    id: 'derivatives',
    label: 'Phái sinh & Quyền chọn',
    icon: 'Layers',
    badgeColor: 'rose',
    description: 'Hợp đồng quyền chọn Call/Put, đồ thị Payoff và Hedging',
    topics: ['derivatives'],
    keywords: ['phái sinh', 'quyền chọn', 'option', 'derivatives', 'hedging', 'call', 'put'],
  },
  {
    id: 'behavioral',
    label: 'Tâm lý học Hành vi',
    icon: 'Brain',
    badgeColor: 'orange',
    description: 'Thiên kiến nhận thức, tâm lý bầy đàn và kỷ luật đầu tư',
    topics: ['behavioral_finance'],
    keywords: ['tâm lý', 'behavioral', 'hành vi', 'kahneman', 'housel', 'thiên kiến'],
  },
  {
    id: 'wealth_saving',
    label: 'Tài chính Cá nhân',
    icon: 'PiggyBank',
    badgeColor: 'teal',
    description: 'Quản lý thu chi, tích sản thụ động và quỹ ETF',
    topics: ['saving', 'budgeting', 'asset_classes', 'etfs_funds'],
    keywords: ['cá nhân', 'tiết kiệm', 'tích sản', 'saving', 'budget', 'lãi kép', 'etf'],
  },
]

export function normalizeDbPaper(row) {
  if (!row) return null
  const authorsList = Array.isArray(row.authors) ? row.authors : []
  const authorsStr = authorsList.length > 0
    ? authorsList.slice(0, 3).join(', ') + (authorsList.length > 3 ? ' và cs.' : '')
    : (row.source === 'nber' ? 'NBER Policy Research' : 'Federal Reserve Board')
  const dateStr = row.published_at
    ? new Date(row.published_at).toLocaleDateString('vi-VN', { year: 'numeric', month: '2-digit', day: '2-digit' })
    : '2026'
  const sourceLabel = row.source === 'arxiv'
    ? 'arXiv (q-fin)'
    : row.source?.includes('fed')
      ? 'Federal Reserve (FED)'
      : row.source === 'nber'
        ? 'NBER Working Paper'
        : 'Research Paper'

  return {
    item_id: row.paper_id,
    paper_id: row.paper_id,
    type: 'paper',
    title: row.title,
    author: authorsStr,
    authors: authorsList,
    date: dateStr,
    published_at: row.published_at,
    source: row.source,
    source_label: sourceLabel,
    category: row.category || 'q-fin',
    topics: Array.isArray(row.topics) ? row.topics : [],
    summary: row.abstract || 'Bài báo nghiên cứu định lượng và kinh tế học tài chính.',
    abstract: row.abstract || '',
    url: row.url,
    pdf_url: row.pdf_url || (row.url?.endsWith('.pdf') ? row.url : null),
    language: row.language || 'en',
  }
}

export function matchesFolder(item, folderId) {
  if (!folderId || folderId === 'all') return true
  const folder = DOCUMENT_FOLDERS.find((f) => f.id === folderId)
  if (!folder) return true

  const itemTopics = Array.isArray(item.topics) ? item.topics : [item.category].filter(Boolean)
  const hasTopicMatch = folder.topics.some((t) => itemTopics.includes(t))
  if (hasTopicMatch) return true

  const text = `${item.title || ''} ${item.summary || ''} ${item.abstract || ''}`.toLowerCase()
  return (folder.keywords || []).some((kw) => text.includes(kw))
}
