/**
 * Quanta DSL Curriculum Structure (AI CIO Quanta Story)
 * 6 thematic sections with 19 structured lessons and 9 practical recipes
 */

export const QUANTA_SECTIONS = [
  {
    id: 'v2-foundation',
    title: 'Cơ sở Quanta & Bắt đầu',
    subtitle: 'Cú pháp Story, Tham số, Kiểu dữ liệu',
    icon: 'Sparkles',
    accent: 'cyan',
    lessons: [
      { id: 'c1-intro', slug: 'quanta-overview', title: 'Quanta là gì? Vì sao học?', subtitle: 'Ngôn ngữ DSL hiện đại, bảo mật cho Quant Trading', level: 'Cơ bản', estimated_min: 6 },
      { id: 'c1-first-strategy', slug: 'chien-luoc-dau-tien', title: 'Chiến lược đầu tiên (EMA Cross)', subtitle: 'Làm quen với framework Quanta Story', level: 'Cơ bản', estimated_min: 10 },
      { id: 'c1-story-expr', slug: 'story-expressions', title: 'Biểu thức Quanta Story', subtitle: 'Cú pháp toán học & logic tự nhiên', level: 'Cơ bản', estimated_min: 8 },
      { id: 'c1-types', slug: 'types-and-inputs', title: 'Kiểu dữ liệu & Tham số', subtitle: 'Series, Scalar, và Lookback an toàn', level: 'Cơ bản', estimated_min: 7 },
      { id: 'c1-fn', slug: 'ham-tu-dinh-nghia', title: 'Hàm: fn', subtitle: 'Tái sử dụng logic với closure', level: 'Trung bình', estimated_min: 5 },
      { id: 'c1-namespaces', slug: 'smart-namespaces', title: 'Smart Namespaces (Cú pháp siêu gọn)', subtitle: 'Gọi Indicator ngắn gọn bằng Namespace', level: 'Cơ bản', estimated_min: 5 },
    ],
  },
  {
    id: 'v2-indicators',
    title: 'Indicators',
    subtitle: 'Trend, Momentum, Volatility, OHLCV',
    icon: 'BarChart3',
    accent: 'cyan',
    lessons: [
      { id: 'c2-ohlcv', slug: 'ohlcv-namespaces', title: 'Namespace: market.*, bar.*, tape.*', subtitle: 'Truy xuất dữ liệu giá và khối lượng', level: 'Cơ bản', estimated_min: 4 },
      { id: 'c2-trend', slug: 'trend-indicators', title: 'Hàm: Trend', subtitle: 'SMA, EMA, HMA, VWMA, WMA', level: 'Cơ bản', estimated_min: 5 },
      { id: 'c2-momentum', slug: 'momentum-indicators', title: 'Hàm: Momentum', subtitle: 'RSI, Stochastic, MACD, ROC, WillR', level: 'Cơ bản', estimated_min: 6 },
      { id: 'c2-volatility', slug: 'volatility-indicators', title: 'Hàm: Volatility', subtitle: 'ATR, Bollinger Bands, Keltner, Donchian', level: 'Trung bình', estimated_min: 7 },
    ],
  },
  {
    id: 'v2-render',
    title: 'Khối Render',
    subtitle: 'Plot Story, Band, Anchored, Profile',
    icon: 'Layers',
    accent: 'cyan',
    lessons: [
      { id: 'c3-verbs', slug: 'render-story-verbs', title: 'Render Story Verbs', subtitle: 'Cú pháp vẽ đồ thị: line, mark, level', level: 'Cơ bản', estimated_min: 8 },
      { id: 'c3-bands', slug: 'bands-and-zones', title: 'Render: Band, Ribbon, Zone, Hist', subtitle: 'Highlight các dải chỉ báo và Regime', level: 'Trung bình', estimated_min: 8 },
      { id: 'c3-anchored', slug: 'anchored-drawings', title: 'Render: Box, Fibo, Trendline', subtitle: 'Neo hình học vào Pivot và thời gian', level: 'Nâng cao', estimated_min: 9 },
      { id: 'c3-vp', slug: 'volume-profiles', title: 'Render: VPVR & VPFR', subtitle: 'Volume Profile dạng Horizontal Histogram', level: 'Nâng cao', estimated_min: 10 },
    ],
  },
  {
    id: 'v2-act-risk',
    title: 'Khối Act & Risk',
    subtitle: 'Enter/Close Story, Signal, Position',
    icon: 'Zap',
    accent: 'cyan',
    lessons: [
      { id: 'c4-act', slug: 'act-english-statements', title: 'Khối Act', subtitle: 'Khối act: enter, close, flatten với wnav', level: 'Trung bình', estimated_min: 7 },
      { id: 'c4-signal', slug: 'allocator-signals', title: 'Signal', subtitle: 'Score, Confidence & Rationale cho Portfolio', level: 'Trung bình', estimated_min: 7 },
      { id: 'c4-risk', slug: 'risk-and-position', title: 'Khối Risk', subtitle: 'Khối risk: và các biến state account', level: 'Trung bình', estimated_min: 6 },
    ],
  },
  {
    id: 'v2-advanced-ai',
    title: 'Nâng cao & AI Tooling',
    subtitle: 'Bẫy thường gặp (Pitfalls) và AI Codegen',
    icon: 'GraduationCap',
    accent: 'cyan',
    lessons: [
      { id: 'c5-pitfalls', slug: 'ai-codegen-pitfalls', title: 'Pitfalls', subtitle: 'Lưu ý khi code nâng cao & tránh Lookahead bias', level: 'Nâng cao', estimated_min: 7 },
      { id: 'c5-codegen', slug: 'ai-codegen-v2', title: 'Làm việc với Trợ lý AI (Quant Studio)', subtitle: 'Cách prompt AI để sinh mã hoàn hảo', level: 'Nâng cao', estimated_min: 6 },
      { id: 'c5-best-practices', slug: 'best-practices', title: 'Best practices cho VN equity', subtitle: 'T+2.5, biên độ trần sàn, lot chẵn & thanh khoản', level: 'Nâng cao', estimated_min: 6 },
    ],
  },
  {
    id: 'v2-recipes',
    title: 'Bài mẫu và ví dụ',
    subtitle: 'Thực hành chiến lược thực chiến VNStock',
    icon: 'Play',
    accent: 'amber',
    lessons: [
      { id: 'r1-ema', slug: 'first-strategy', title: 'Bài 1 — EMA cross', subtitle: 'Chiến lược giao cắt xu hướng cơ bản', level: 'Cơ bản', estimated_min: 8 },
      { id: 'r2-bb-rsi', slug: 'bb-rsi-study', title: 'Bài 2 — Study BB + RSI', subtitle: 'Biểu đồ kỹ thuật đa panel chuyên sâu', level: 'Cơ bản', estimated_min: 8 },
      { id: 'r3-mean-rev', slug: 'regime-mean-reversion', title: 'Bài 3 — Mean reversion + regime', subtitle: 'Bắt đáy đảo chiều trong thị trường Sideway', level: 'Trung bình', estimated_min: 10 },
      { id: 'r4-donchian', slug: 'breakout-with-volume', title: 'Bài 4 — Donchian + volume', subtitle: 'Bứt phá đỉnh kèm bùng nổ khối lượng', level: 'Trung bình', estimated_min: 10 },
      { id: 'r5-trailing', slug: 'exit-management', title: 'Bài 5 — Trailing ATR exit', subtitle: 'Chốt lời động và kiểm soát rủi ro chặt chẽ', level: 'Trung bình', estimated_min: 9 },
      { id: 'r6-pivot', slug: 'pivot-trendline-chart', title: 'Bài 6 — Pivot + trendline', subtitle: 'Tự động kẻ đường xu hướng theo đỉnh đáy', level: 'Nâng cao', estimated_min: 12 },
      { id: 'r7-mom121', slug: 'momentum-12-1', title: 'Ví dụ — Momentum 12-1', subtitle: 'Chiến lược đà tăng trưởng chu kỳ 12 tháng', level: 'Nâng cao', estimated_min: 8 },
      { id: 'r8-vol-target', slug: 'volatility-targeting', title: 'Ví dụ — Volatility targeting', subtitle: 'Cân bằng tỷ trọng theo biến động thị trường', level: 'Nâng cao', estimated_min: 10 },
      { id: 'r9-marker', slug: 'multi-condition-marker', title: 'Ví dụ — Marker đa điều kiện', subtitle: 'Đánh dấu điểm nổ vol & phân kỳ chỉ báo', level: 'Trung bình', estimated_min: 8 },
    ],
  },
]

export const TUTORIAL_FAST_TRACK = [
  { num: 1, slug: 'quanta-overview', title: 'Quanta là gì? Vì sao học?' },
  { num: 2, slug: 'chien-luoc-dau-tien', title: 'Chiến lược đầu tiên (EMA Cross)' },
  { num: 3, slug: 'story-expressions', title: 'Biểu thức Quanta Story' },
  { num: 4, slug: 'types-and-inputs', title: 'Kiểu dữ liệu & Tham số' },
  { num: 5, slug: 'ham-tu-dinh-nghia', title: 'Hàm: fn' },
]

export function findQuantaLesson(slugOrId) {
  for (const sec of QUANTA_SECTIONS) {
    for (const l of sec.lessons) {
      if (l.slug === slugOrId || l.id === slugOrId) {
        return { ...l, sectionId: sec.id, sectionTitle: sec.title }
      }
    }
  }
  return null
}
