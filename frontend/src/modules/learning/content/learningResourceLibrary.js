const LOCAL_ASSET_BASE = '/learning-assets'

function localVideo(file) {
  return `${LOCAL_ASSET_BASE}/videos/${file}`
}

function localBook(file) {
  return `${LOCAL_ASSET_BASE}/books/${file}`
}

const TIER_PRESETS = {
  financial_basics: {
    videos: [
      {
        id: 'v-fin-1',
        title: 'Video nhanh: Quản lý dòng tiền 101',
        duration: '4 phút',
        href: localVideo('cashflow-101.mp4'),
      },
    ],
    books: [
      {
        id: 'b-fin-1',
        title: 'Book note: The Psychology of Money',
        summary: 'Tập trung vào hành vi tiền bạc bền vững hơn là tối ưu ngắn hạn.',
        href: localBook('psychology-of-money-notes.pdf'),
      },
    ],
    practical: [
      {
        id: 'p-fin-1',
        title: 'Mở Financial Health và kiểm tra cash-flow baseline',
        ctaLabel: 'Mở Financial Health',
        ctaType: 'financial_health',
      },
    ],
  },
  basic_investing_literacy: {
    videos: [
      {
        id: 'v-inv-1',
        title: 'Video nhanh: Risk, drawdown và volatility',
        duration: '5 phút',
        href: localVideo('risk-drawdown-basics.mp4'),
      },
    ],
    books: [
      {
        id: 'b-inv-1',
        title: 'Book note: The Little Book of Common Sense Investing',
        summary: 'Ưu tiên kỷ luật, chi phí thấp và kỳ vọng thực tế.',
        href: localBook('common-sense-investing-notes.pdf'),
      },
    ],
    practical: [
      {
        id: 'p-inv-1',
        title: 'Mở Guided Investing để đọc rủi ro bằng ngôn ngữ dễ hiểu',
        ctaLabel: 'Mở Guided Investing',
        ctaType: 'guided_investing',
      },
    ],
  },
  product_tool_literacy: {
    videos: [
      {
        id: 'v-tool-1',
        title: 'Video nhanh: Đọc score và trust banner trong app',
        duration: '3 phút',
        href: localVideo('risk-score-tool-walkthrough.mp4'),
      },
    ],
    books: [
      {
        id: 'b-tool-1',
        title: 'Book note: Systems Thinking for Finance',
        summary: 'Nhìn hệ thống tổng thể trước khi phản ứng theo từng chỉ số lẻ.',
        href: localBook('systems-thinking-finance-notes.pdf'),
      },
    ],
    practical: [
      {
        id: 'p-tool-1',
        title: 'Mở Insights để xem dữ liệu + lời giải thích cùng lúc',
        ctaLabel: 'Mở Insights',
        ctaType: 'insights',
      },
    ],
  },
}

const LESSON_OVERRIDES = {
  'money-basics-101': {
    videos: [
      {
        id: 'v-money-1',
        title: 'Video: Tiền cơ bản cho người mới đi làm',
        duration: '6 phút',
        href: localVideo('money-basics-starter.mp4'),
      },
    ],
  },
  'compounding-basics-101': {
    books: [
      {
        id: 'b-compound-1',
        title: 'Book note: Atomic Habits (góc nhìn kỷ luật tài chính)',
        summary: 'Lãi kép cần thói quen đều đặn, không cần “đột phá” mỗi tuần.',
        href: localBook('atomic-habits-finance-notes.pdf'),
      },
    ],
  },
  'tool-goals-101': {
    practical: [
      {
        id: 'p-goal-1',
        title: 'Tạo mục tiêu đầu tiên và chọn pace tháng',
        ctaLabel: 'Mở Goals',
        ctaType: 'goals',
      },
    ],
  },
}

export const LEARN_QUICK_PROMPTS = [
  'Tóm tắt bài này trong 3 ý đơn giản.',
  'Bài này liên quan gì đến mục tiêu tài chính của tôi?',
  'Sau bài này tôi nên làm bước nào trong app?',
]

export function getLessonResourceBundle(lesson) {
  if (!lesson) {
    return {
      videos: [],
      books: [],
      practical: [],
    }
  }
  const preset = TIER_PRESETS[lesson.tier] || TIER_PRESETS.financial_basics
  const overrides = LESSON_OVERRIDES[lesson.lesson_id] || {}
  return {
    videos: overrides.videos || preset.videos,
    books: overrides.books || preset.books,
    practical: overrides.practical || preset.practical,
  }
}
