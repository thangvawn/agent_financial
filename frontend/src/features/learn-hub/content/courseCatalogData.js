/**
 * Demo course catalog & book library data — Coursera-style structure.
 */

const DEMO_VIDEO = '/learning-assets/videos/tap-1-nhap-mon-tai-chinh.mp4'

export const COURSE_CATEGORIES = [
  { id: 'all', label: 'Tất cả' },
  { id: 'finance', label: 'Tài chính cơ bản' },
  { id: 'investing', label: 'Đầu tư' },
  { id: 'analysis', label: 'Phân tích' },
  { id: 'tools', label: 'Công cụ' },
]

export const DEMO_COURSES = [
  {
    course_id: 'fin-101',
    title: 'Nhập môn Tài chính Cá nhân',
    description: 'Hiểu nền tảng quản lý tiền bạc, lập ngân sách, quỹ khẩn cấp và lãi kép. Khóa học dành cho người mới bắt đầu.',
    instructor: 'Northstar Finance Lab',
    category: 'finance',
    difficulty: 'Cơ bản',
    total_duration: '45 phút',
    lesson_count: 6,
    thumbnail_image: '/learning-assets/images/course_fin101_thumb_1784704535025.png',
    sections: [
      {
        section_id: 'fin-101-s1',
        title: 'Nền tảng tài chính',
        lessons: [
          { lesson_id: 'fin-101-l1', title: 'Tập 1: Nhập môn tài chính', duration: '12:30', video_url: DEMO_VIDEO },
          { lesson_id: 'fin-101-l2', title: 'Tập 2: Ngân sách cá nhân', duration: '8:45', video_url: DEMO_VIDEO },
          { lesson_id: 'fin-101-l3', title: 'Tập 3: Quỹ khẩn cấp', duration: '7:20', video_url: DEMO_VIDEO },
        ],
      },
      {
        section_id: 'fin-101-s2',
        title: 'Lãi kép và tiết kiệm',
        lessons: [
          { lesson_id: 'fin-101-l4', title: 'Tập 4: Sức mạnh lãi kép', duration: '9:10', video_url: DEMO_VIDEO },
          { lesson_id: 'fin-101-l5', title: 'Tập 5: Chiến lược tiết kiệm', duration: '6:50', video_url: DEMO_VIDEO },
          { lesson_id: 'fin-101-l6', title: 'Tập 6: Tổng kết & bài tập', duration: '5:00', video_url: DEMO_VIDEO },
        ],
      },
    ],
  },
  {
    course_id: 'inv-201',
    title: 'Đầu tư Chứng khoán cho Người mới',
    description: 'Từ zero đến hero: hiểu thị trường chứng khoán, cách mở tài khoản, đọc bảng giá và đặt lệnh đầu tiên.',
    instructor: 'Northstar Finance Lab',
    category: 'investing',
    difficulty: 'Cơ bản',
    total_duration: '1 giờ 20 phút',
    lesson_count: 8,
    thumbnail_image: '/learning-assets/images/course_inv201_thumb_1784704545270.png',
    sections: [
      {
        section_id: 'inv-201-s1',
        title: 'Hiểu thị trường',
        lessons: [
          { lesson_id: 'inv-201-l1', title: 'Thị trường chứng khoán là gì?', duration: '10:00', video_url: DEMO_VIDEO },
          { lesson_id: 'inv-201-l2', title: 'Các loại chứng khoán', duration: '8:30', video_url: DEMO_VIDEO },
          { lesson_id: 'inv-201-l3', title: 'Đọc bảng giá cơ bản', duration: '12:00', video_url: DEMO_VIDEO },
          { lesson_id: 'inv-201-l4', title: 'Lệnh mua bán và khớp lệnh', duration: '9:20', video_url: DEMO_VIDEO },
        ],
      },
      {
        section_id: 'inv-201-s2',
        title: 'Chiến lược cơ bản',
        lessons: [
          { lesson_id: 'inv-201-l5', title: 'DCA — trung bình giá', duration: '11:00', video_url: DEMO_VIDEO },
          { lesson_id: 'inv-201-l6', title: 'Phân bổ danh mục', duration: '10:30', video_url: DEMO_VIDEO },
          { lesson_id: 'inv-201-l7', title: 'Quản lý rủi ro', duration: '9:45', video_url: DEMO_VIDEO },
          { lesson_id: 'inv-201-l8', title: 'Tâm lý đầu tư', duration: '8:55', video_url: DEMO_VIDEO },
        ],
      },
    ],
  },
  {
    course_id: 'bctc-301',
    title: 'Đọc hiểu Báo cáo Tài chính',
    description: 'Phân tích bảng cân đối, kết quả kinh doanh và lưu chuyển tiền tệ. Kết nối trực tiếp với module BCTC Analysis.',
    instructor: 'Northstar Finance Lab',
    category: 'analysis',
    difficulty: 'Trung bình',
    total_duration: '2 giờ',
    lesson_count: 7,
    thumbnail_image: '/learning-assets/images/course_bctc301_thumb_1784704555922.png',
    sections: [
      {
        section_id: 'bctc-301-s1',
        title: 'Ba báo cáo chính',
        lessons: [
          { lesson_id: 'bctc-301-l1', title: 'Tổng quan BCTC', duration: '15:00', video_url: DEMO_VIDEO },
          { lesson_id: 'bctc-301-l2', title: 'Bảng cân đối kế toán', duration: '18:30', video_url: DEMO_VIDEO },
          { lesson_id: 'bctc-301-l3', title: 'Kết quả kinh doanh', duration: '16:20', video_url: DEMO_VIDEO },
          { lesson_id: 'bctc-301-l4', title: 'Lưu chuyển tiền tệ', duration: '14:40', video_url: DEMO_VIDEO },
        ],
      },
      {
        section_id: 'bctc-301-s2',
        title: 'Phân tích chỉ số',
        lessons: [
          { lesson_id: 'bctc-301-l5', title: 'Chỉ số thanh khoản', duration: '12:00', video_url: DEMO_VIDEO },
          { lesson_id: 'bctc-301-l6', title: 'Chỉ số sinh lời', duration: '13:30', video_url: DEMO_VIDEO },
          { lesson_id: 'bctc-301-l7', title: 'Case study thực tế', duration: '20:00', video_url: DEMO_VIDEO },
        ],
      },
    ],
  },
  {
    course_id: 'macro-401',
    title: 'Phân tích Kinh tế Vĩ mô',
    description: 'GDP, lạm phát, lãi suất, tỷ giá và tác động đến thị trường tài chính Việt Nam. Dành cho người đã có nền tảng.',
    instructor: 'Northstar Finance Lab',
    category: 'analysis',
    difficulty: 'Nâng cao',
    total_duration: '2 giờ 30 phút',
    lesson_count: 8,
    thumbnail_image: '/learning-assets/images/course_macro401_thumb_1784704573477.png',
    sections: [
      {
        section_id: 'macro-401-s1',
        title: 'Các chỉ số vĩ mô',
        lessons: [
          { lesson_id: 'macro-401-l1', title: 'GDP và tăng trưởng kinh tế', duration: '18:00', video_url: DEMO_VIDEO },
          { lesson_id: 'macro-401-l2', title: 'Lạm phát và CPI', duration: '16:30', video_url: DEMO_VIDEO },
          { lesson_id: 'macro-401-l3', title: 'Chính sách tiền tệ', duration: '20:00', video_url: DEMO_VIDEO },
          { lesson_id: 'macro-401-l4', title: 'Tỷ giá hối đoái', duration: '14:20', video_url: DEMO_VIDEO },
        ],
      },
      {
        section_id: 'macro-401-s2',
        title: 'Tác động thị trường',
        lessons: [
          { lesson_id: 'macro-401-l5', title: 'Fed và tác động toàn cầu', duration: '19:00', video_url: DEMO_VIDEO },
          { lesson_id: 'macro-401-l6', title: 'Kinh tế Việt Nam', duration: '17:30', video_url: DEMO_VIDEO },
          { lesson_id: 'macro-401-l7', title: 'Đọc lịch kinh tế', duration: '12:00', video_url: DEMO_VIDEO },
          { lesson_id: 'macro-401-l8', title: 'Case study: Chu kỳ kinh tế', duration: '22:00', video_url: DEMO_VIDEO },
        ],
      },
    ],
  },
  {
    course_id: 'risk-202',
    title: 'Quản lý Rủi ro Đầu tư',
    description: 'Risk, drawdown, volatility và các công cụ đo lường rủi ro. Áp dụng vào danh mục thực tế qua Simulation Lab.',
    instructor: 'Northstar Finance Lab',
    category: 'investing',
    difficulty: 'Trung bình',
    total_duration: '1 giờ 30 phút',
    lesson_count: 6,
    thumbnail_image: '/learning-assets/images/course_inv201_thumb_1784704545270.png',
    sections: [
      {
        section_id: 'risk-202-s1',
        title: 'Các loại rủi ro',
        lessons: [
          { lesson_id: 'risk-202-l1', title: 'Rủi ro hệ thống vs phi hệ thống', duration: '14:00', video_url: DEMO_VIDEO },
          { lesson_id: 'risk-202-l2', title: 'Đo lường volatility', duration: '12:30', video_url: DEMO_VIDEO },
          { lesson_id: 'risk-202-l3', title: 'Max drawdown và Sharpe ratio', duration: '15:20', video_url: DEMO_VIDEO },
        ],
      },
      {
        section_id: 'risk-202-s2',
        title: 'Ứng dụng thực tế',
        lessons: [
          { lesson_id: 'risk-202-l4', title: 'Hedging cơ bản', duration: '13:10', video_url: DEMO_VIDEO },
          { lesson_id: 'risk-202-l5', title: 'Position sizing', duration: '11:50', video_url: DEMO_VIDEO },
          { lesson_id: 'risk-202-l6', title: 'Backtest chiến lược', duration: '16:00', video_url: DEMO_VIDEO },
        ],
      },
    ],
  },
  {
    course_id: 'tool-101',
    title: 'Sử dụng Northstar Platform',
    description: 'Hướng dẫn toàn diện cách sử dụng các module: Market Terminal, BCTC Analysis, Simulation Lab và News.',
    instructor: 'Northstar Finance Lab',
    category: 'tools',
    difficulty: 'Cơ bản',
    total_duration: '50 phút',
    lesson_count: 5,
    thumbnail_image: '/learning-assets/images/course_fin101_thumb_1784704535025.png',
    sections: [
      {
        section_id: 'tool-101-s1',
        title: 'Các module chính',
        lessons: [
          { lesson_id: 'tool-101-l1', title: 'Tổng quan Northstar Platform', duration: '8:00', video_url: DEMO_VIDEO },
          { lesson_id: 'tool-101-l2', title: 'Market Terminal & Portfolio', duration: '12:00', video_url: DEMO_VIDEO },
          { lesson_id: 'tool-101-l3', title: 'BCTC Analysis walkthrough', duration: '10:30', video_url: DEMO_VIDEO },
          { lesson_id: 'tool-101-l4', title: 'News desk & bộ lọc', duration: '9:20', video_url: DEMO_VIDEO },
          { lesson_id: 'tool-101-l5', title: 'Simulation Lab & Backtest', duration: '11:00', video_url: DEMO_VIDEO },
        ],
      },
    ],
  },
]

export const DEMO_BOOKS = [
  {
    book_id: 'b-psychology',
    title: 'Tâm Lý Học Về Tiền',
    original_title: 'The Psychology of Money',
    author: 'Morgan Housel',
    category: 'finance',
    pages: 280,
    read_time: '4 giờ',
    rating: 4.9,
    cover_image: '/learning-assets/images/book_psychology_cover_1784704922885.png',
    cover_color: 'linear-gradient(135deg, #0d9488 0%, #115e59 100%)',
    summary: 'Tập trung vào hành vi tiền bạc bền vững hơn là tối ưu ngắn hạn. Lãi kép cần thói quen đều đặn duy trì nhiều năm.',
    pdf_url: '/learning-assets/books/psychology-of-money-notes.html',
    key_takeaways: [
      'Sự tự do tài chính quan trọng hơn sự giàu có phô trương.',
      'Lợi nhuận tốt không phải là cao nhất, mà là duy trì được lâu nhất.',
      'Tiết kiệm là khoảng chênh lệch giữa cái bạn kiếm và cái bạn tiêu.',
    ],
  },
  {
    book_id: 'b-common-sense',
    title: 'Đầu Tư Chứng Khoán Theo Chỉ Số',
    original_title: 'The Little Book of Common Sense Investing',
    author: 'John C. Bogle',
    category: 'investing',
    pages: 320,
    read_time: '5 giờ',
    rating: 4.8,
    cover_image: '/learning-assets/images/book_bogle_cover_1784704934019.png',
    cover_color: 'linear-gradient(135deg, #6366f1 0%, #3730a3 100%)',
    summary: 'Ưu tiên kỷ luật, chi phí thấp, đầu tư chỉ số và giữ kỳ vọng thực tế thay vì cố đánh bại thị trường.',
    pdf_url: '/learning-assets/books/common-sense-investing-notes.html',
    key_takeaways: [
      'Tìm toàn bộ haystack thay vì tìm needle trong haystack.',
      'Chi phí đầu tư thấp là lợi thế cạnh tranh dài hạn lớn nhất.',
      'Sức mạnh của việc nắm giữ danh mục đa dạng toàn thị trường.',
    ],
  },
  {
    book_id: 'b-financial-analysis',
    title: 'Đọc Báo Cáo Tài Chính Nhận Biết Rủi Ro',
    original_title: 'Financial Statements & Risk Analysis',
    author: 'Northstar Research Team',
    category: 'analysis',
    pages: 210,
    read_time: '3.5 giờ',
    rating: 4.9,
    cover_image: '/learning-assets/images/course_bctc301_thumb_1784704555922.png',
    cover_color: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
    summary: 'Nhìn hệ thống tổng thể BCTC trước khi phản ứng theo từng chỉ số lẻ. Phát hiện các red flag báo cáo tài chính.',
    pdf_url: '/learning-assets/books/systems-thinking-finance-notes.html',
    key_takeaways: [
      'Dòng tiền từ hoạt động kinh doanh (CFO) là thước đo độ trung thực.',
      'Các khoản phải thu tăng nhanh hơn doanh thu là dấu hiệu cảnh báo.',
      'Tỷ lệ nợ ròng / EBITDA đánh giá khả năng chịu đựng suy thoái.',
    ],
  },
  {
    book_id: 'b-atomic-finance',
    title: 'Atomic Habits — Góc Nhìn Tài Chính',
    original_title: 'Atomic Habits for Financial Success',
    author: 'James Clear (Adapted)',
    category: 'finance',
    pages: 195,
    read_time: '3 giờ',
    rating: 4.7,
    cover_image: '/learning-assets/images/course_fin101_thumb_1784704535025.png',
    cover_color: 'linear-gradient(135deg, #8b5cf6 0%, #5b21b6 100%)',
    summary: 'Tự động hóa thói quen đầu tư hàng tháng (DCA) và loại bỏ rào cản tâm lý khi duy trì kỷ luật tích lũy tài sản.',
    pdf_url: '/learning-assets/books/psychology-of-money-notes.html',
    key_takeaways: [
      '1% tốt hơn mỗi ngày tích lũy thành kết quả khổng lồ sau 5 năm.',
      'Tập trung vào hệ thống (quy trình tích lũy) thay vì chỉ mục tiêu.',
      'Tự động hóa lệnh chuyển khoản ngay khi nhận lương.',
    ],
  },
]

export function findCourseById(courseId) {
  return DEMO_COURSES.find((c) => c.course_id === courseId) || null
}

export function getAllLessons(course) {
  if (!course) return []
  return course.sections.flatMap((s) => s.lessons)
}

export function findLessonIndex(course, lessonId) {
  const all = getAllLessons(course)
  return all.findIndex((l) => l.lesson_id === lessonId)
}

const DIFFICULTY_ORDER = { 'Cơ bản': 0, 'Trung bình': 1, 'Nâng cao': 2 }

export function filterCourses(courses, { category, search }) {
  let result = courses
  if (category && category !== 'all') {
    result = result.filter((c) => c.category === category)
  }
  if (search && search.trim()) {
    const q = search.toLowerCase().trim()
    result = result.filter((c) => {
      const blob = `${c.title} ${c.description} ${c.instructor} ${c.category}`.toLowerCase()
      return blob.includes(q)
    })
  }
  return result.sort((a, b) => (DIFFICULTY_ORDER[a.difficulty] ?? 9) - (DIFFICULTY_ORDER[b.difficulty] ?? 9))
}
