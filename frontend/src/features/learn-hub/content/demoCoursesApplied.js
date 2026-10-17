/** Applied course masterclasses: Bonds, Derivatives, FinTech, Psychology, Wealth */

function yt(id) {
  return `https://www.youtube.com/watch?v=${id}`
}

function ytThumb(id) {
  return `https://img.youtube.com/vi/${id}/hqdefault.jpg`
}

function l(id, title, duration, videoId) {
  return { lesson_id: id, title, duration, video_url: yt(videoId), video_id: videoId }
}

function sec(id, title, lessons) {
  return { section_id: id, title, lessons }
}

export const APPLIED_COURSES = [
  {
    course_id: 'bond-601',
    title: 'Thị trường Trái phiếu & Đường cong Lợi suất',
    description: 'Thị trường thu nhập cố định, định giá trái phiếu, mối quan hệ nghịch đảo giữa giá và lãi suất.',
    instructor: 'Wharton School • Khan Academy',
    category: 'finance',
    difficulty: 'Trung bình',
    total_duration: '1 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('Qh-M3_L4xYk'),
    sections: [
      sec('bond-s1', 'Bản chất & Định giá Trái phiếu', [
        l('bond-l1', 'Khái niệm & Cơ chế vận hành Trái phiếu (Khan)', '15 phút', 'Qh-M3_L4xYk'),
        l('bond-l2', 'Mối quan hệ giữa Giá trái phiếu và Lãi suất', '12 phút', 'vAdn7aLHpO0'),
      ]),
      sec('bond-s2', 'Đường cong Lợi suất & Định giá Dòng tiền', [
        l('bond-l3', 'Đường cong lợi suất Yield Curve & Tín hiệu vĩ mô', '18 phút', 'b_cAxh44aNQ'),
        l('bond-l4', 'Giá trị thời gian của tiền & Chiết khấu (Wharton)', '20 phút', 'UcAY6qRHlw0'),
      ]),
    ],
  },
  {
    course_id: 'deriv-701',
    title: 'Thị trường Phái sinh & Chiến lược Quyền chọn',
    description: 'Hợp đồng quyền chọn (Options) Call/Put, đồ thị hoàn trả Payoff và chiến lược phòng hộ.',
    instructor: 'Khan Academy • InTheMoney Derivatives Lab',
    category: 'tools',
    difficulty: 'Nâng cao',
    total_duration: '1,2 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('7PM4rNDr4oI'),
    sections: [
      sec('deriv-s1', 'Căn bản Quyền chọn & Hợp đồng Phái sinh', [
        l('deriv-l1', 'Nhập môn Giao dịch Quyền chọn Options', '25 phút', '7PM4rNDr4oI'),
        l('deriv-l2', 'Hợp đồng Quyền chọn Mua - Call Options (Khan)', '15 phút', 'nnl3x1wo25g'),
      ]),
      sec('deriv-s2', 'Quyền chọn Bán & Chiến lược Phòng hộ', [
        l('deriv-l3', 'Hợp đồng Quyền chọn Bán - Put Options (Khan)', '15 phút', '6CUcgUeQS-w'),
        l('deriv-l4', 'Chiến lược Phòng hộ Hedging & Payoff Diagrams', '15 phút', 'WFuLVSz6n8M'),
      ]),
    ],
  },
  {
    course_id: 'fintech-801',
    title: 'Công nghệ FinTech, Blockchain & Web3 Finance',
    description: 'Sổ cái phân tán, công nghệ blockchain, hàm băm mật mã học và tương lai thanh toán số.',
    instructor: 'Prof. Gary Gensler (MIT) • 3Blue1Brown',
    category: 'tools',
    difficulty: 'Trung bình',
    total_duration: '1,4 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('5auv_xrvoJk'),
    sections: [
      sec('fintech-s1', 'Kiến trúc Tiền tệ & Blockchain Nền tảng', [
        l('fintech-l1', 'Blockchain và Bản chất Tiền tệ (Gary Gensler)', '35 phút', '5auv_xrvoJk'),
        l('fintech-l2', 'Bản chất Thuật toán Bitcoin & Sổ cái Phân tán', '25 phút', 'bBC-nXj3Ng4'),
      ]),
      sec('fintech-s2', 'Mật mã học & Tài chính Phi tập trung', [
        l('fintech-l3', 'Hàm băm Mật mã học & Bảo mật Giao dịch', '12 phút', 'SSo_EIwHSd4'),
        l('fintech-l4', 'Hợp đồng Thông minh & Cơ chế Đồng thuận (MIT)', '10 phút', '5auv_xrvoJk'),
      ]),
    ],
  },
  {
    course_id: 'psych-901',
    title: 'Tâm lý học Hành vi & Kỷ luật Giao dịch',
    description: 'Thiên kiến nhận thức, tâm lý sợ mất mát (loss aversion), bẫy chi phí chìm và kỷ luật đầu tư.',
    instructor: 'Daniel Kahneman Research • Crash Course',
    category: 'investing',
    difficulty: 'Trung bình',
    total_duration: '45 phút',
    lesson_count: 4,
    thumbnail_image: ytThumb('dqxQ3E1bubI'),
    sections: [
      sec('psych-s1', 'Thiên kiến Nhận thức & Kinh tế học Hành vi', [
        l('psych-l1', 'Kinh tế học Hành vi & Tâm lý Ra quyết định', '10 phút', 'dqxQ3E1bubI'),
        l('psych-l2', 'Thiên kiến Tránh lỗ & Chiến lược Trung bình giá', '8 phút', 'vLTdlN7VJTM'),
      ]),
      sec('psych-s2', 'Tâm lý Đám đông & Kỷ luật Giao dịch', [
        l('psych-l3', 'Tâm lý Đám đông trong Khủng hoảng & Bong bóng', '11 phút', 'qOP2V_np2c0'),
        l('psych-l4', 'Kiểm soát Cảm xúc & Kỷ luật Cắt lỗ Thực chiến', '5 phút', 'CMQLdJa64Wk'),
      ]),
    ],
  },
  {
    course_id: 'wealth-1001',
    title: 'Quản lý Tài chính Cá nhân & Tích sản Thông minh',
    description: 'Nền tảng tài chính cá nhân, sức mạnh lãi kép, phân bổ tài sản đa lớp và chiến lược tích sản.',
    instructor: 'Sal Khan • Ben Felix (PWL Capital)',
    category: 'finance',
    difficulty: 'Cơ bản',
    total_duration: '42 phút',
    lesson_count: 4,
    thumbnail_image: ytThumb('79HS3N1IBt8'),
    sections: [
      sec('wealth-s1', 'Sức mạnh Lãi kép & Giá trị Tiền tệ', [
        l('wealth-l1', 'Tính toán Lãi đơn & Lãi kép thực tế (Khan)', '6 phút', '79HS3N1IBt8'),
        l('wealth-l2', 'Lãi suất & Giá trị Thời gian của Tiền (Khan)', '8 phút', 'Rm6UdfRs3gw'),
      ]),
      sec('wealth-s2', 'Chiến lược Tích sản & Quản lý Danh mục', [
        l('wealth-l3', 'Quỹ Mở vs Quỹ Hoán đổi Danh mục ETF', '10 phút', 'HghsQN89w9k'),
        l('wealth-l4', 'Xây dựng Danh mục Tài sản Đa tầng Bền vững', '12 phút', '1FXuMs6YRCY'),
      ]),
    ],
  },
]
