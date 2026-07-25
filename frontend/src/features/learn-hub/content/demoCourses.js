/** Learn Hub course catalog — YouTube curated (IDs verified live). */

function yt(id) {
  return `https://www.youtube.com/watch?v=${id}`
}

function ytThumb(id) {
  return `https://img.youtube.com/vi/${id}/hqdefault.jpg`
}

function lesson(id, title, duration, videoId) {
  return { lesson_id: id, title, duration, video_url: yt(videoId), video_id: videoId }
}

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
    description: 'Nền tảng quản lý tiền, lãi kép và cách nền kinh tế vận hành.',
    instructor: 'Ray Dalio · Khan Academy · The Wealth Workshop',
    category: 'finance',
    difficulty: 'Cơ bản',
    total_duration: '~1.5 giờ',
    lesson_count: 5,
    thumbnail_image: ytThumb('PHe0bXAIuk0'),
    sections: [
      {
        section_id: 'fin-101-s1',
        title: 'Nền tảng',
        lessons: [
          lesson('fin-101-l1', 'Máy kinh tế vận hành thế nào (Dalio)', '31 phút', 'PHe0bXAIuk0'),
          lesson('fin-101-l2', 'Các bước quản lý tiền cơ bản', '12 phút', 'UcAY6qRHlw0'),
          lesson('fin-101-l3', 'Lãi kép — phần mở đầu (Khan)', '8 phút', 'Rm6UdfRs3gw'),
        ],
      },
      {
        section_id: 'fin-101-s2',
        title: 'Tính toán & thói quen',
        lessons: [
          lesson('fin-101-l4', 'Tính lãi đơn & lãi kép (Khan)', '6 phút', '79HS3N1IBt8'),
          lesson('fin-101-l5', 'Thị trường chứng khoán hoạt động ra sao (TED-Ed)', '5 phút', 'p7HKvqRI_Bo'),
        ],
      },
    ],
  },
  {
    course_id: 'inv-201',
    title: 'Đầu tư cho Người mới',
    description: 'Cổ phiếu, chỉ số, ETF, đa dạng hoá và kỷ luật đầu tư dài hạn.',
    instructor: 'TED-Ed · Plain Bagel · Ben Felix · Netflix',
    category: 'investing',
    difficulty: 'Cơ bản',
    total_duration: '~2 giờ',
    lesson_count: 6,
    thumbnail_image: ytThumb('ZCFkWDdmXG8'),
    sections: [
      {
        section_id: 'inv-201-s1',
        title: 'Hiểu thị trường',
        lessons: [
          lesson('inv-201-l1', 'Giải thích thị trường chứng khoán (Netflix Explained)', '19 phút', 'ZCFkWDdmXG8'),
          lesson('inv-201-l2', 'Nhà đầu tư chọn cổ phiếu thế nào (TED-Ed)', '5 phút', 'CMQLdJa64Wk'),
          lesson('inv-201-l3', 'Chỉ số & quỹ chỉ số (Plain Bagel)', '12 phút', '5A4lp_oZ5zg'),
        ],
      },
      {
        section_id: 'inv-201-s2',
        title: 'Danh mục & kỷ luật',
        lessons: [
          lesson('inv-201-l4', 'Từ khoá Mutual Fund / ETF', '10 phút', 'HghsQN89w9k'),
          lesson('inv-201-l5', 'Đa dạng hoá quốc tế (Ben Felix)', '12 phút', '1FXuMs6YRCY'),
          lesson('inv-201-l6', 'Factor Investing với ETF (Ben Felix)', '14 phút', 'jKWbW7Wgm0w'),
        ],
      },
    ],
  },
  {
    course_id: 'bctc-301',
    title: 'Đọc hiểu Báo cáo & Định giá',
    description: 'BCTC cơ bản, trái phiếu và tư duy tài chính từ các nguồn mở.',
    instructor: 'Big Think · Investopedia-style · Crash Course',
    category: 'analysis',
    difficulty: 'Trung bình',
    total_duration: '~1 giờ',
    lesson_count: 5,
    thumbnail_image: ytThumb('Fi1wkUczuyk'),
    sections: [
      {
        section_id: 'bctc-301-s1',
        title: 'Báo cáo & công cụ',
        lessons: [
          lesson('bctc-301-l1', 'Báo cáo tài chính trong 8 phút', '8 phút', 'Fi1wkUczuyk'),
          lesson('bctc-301-l2', 'Trái phiếu cơ bản', '6 phút', 'vAdn7aLHpO0'),
          lesson('bctc-301-l3', 'Ackman: nền tảng finance & investing', '45 phút', 'WEDIj9JBTC8'),
        ],
      },
      {
        section_id: 'bctc-301-s2',
        title: 'Hành vi',
        lessons: [
          lesson('bctc-301-l4', 'Behavioral Economics (Crash Course)', '10 phút', 'dqxQ3E1bubI'),
          lesson('bctc-301-l5', 'Dollar Cost Averaging', '8 phút', 'vLTdlN7VJTM'),
        ],
      },
    ],
  },
  {
    course_id: 'macro-401',
    title: 'Kinh tế vĩ mô & Chu kỳ',
    description: 'GDP, lạm phát và khủng hoảng tư bản — góc nhìn giáo dục mở.',
    instructor: 'RSA · Econ channels · Khan Academy',
    category: 'analysis',
    difficulty: 'Trung bình',
    total_duration: '~1 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('AaR1mPrdbTc'),
    sections: [
      {
        section_id: 'macro-401-s1',
        title: 'Vĩ mô căn bản',
        lessons: [
          lesson('macro-401-l1', 'Lạm phát là gì (Khan)', '8 phút', 'AaR1mPrdbTc'),
          lesson('macro-401-l2', 'GDP giải thích đầy đủ', '15 phút', '7GZrpVlLXRA'),
          lesson('macro-401-l3', 'Khủng hoảng tư bản (RSA Animate)', '11 phút', 'qOP2V_np2c0'),
          lesson('macro-401-l4', 'Máy kinh tế — bản vietsub', '31 phút', 'XggDwAftez4'),
        ],
      },
    ],
  },
  {
    course_id: 'quant-501',
    title: 'Công cụ định lượng căn bản',
    description: 'Mô phỏng Monte Carlo và trực giác toán hữu ích cho phân tích rủi ro.',
    instructor: 'Quant explainers · 3Blue1Brown',
    category: 'tools',
    difficulty: 'Nâng cao',
    total_duration: '~25 phút',
    lesson_count: 3,
    thumbnail_image: ytThumb('psOYFdx838E'),
    sections: [
      {
        section_id: 'quant-501-s1',
        title: 'Thực hành',
        lessons: [
          lesson('quant-501-l1', 'Monte Carlo Simulation trong 5 phút', '5 phút', 'psOYFdx838E'),
          lesson('quant-501-l2', 'Fourier Transform — trực giác', '20 phút', 'spUNpyF58BY'),
          lesson('quant-501-l3', 'Bài toán đếm bất ngờ (3Blue1Brown)', '5 phút', 'HEfHFsfGXjs'),
        ],
      },
    ],
  },
]
