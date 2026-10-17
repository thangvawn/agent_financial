/** Foundation course masterclasses: Macro, BCTC, Valuation, Stock, Quant */

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

export const FOUNDATION_COURSES = [
  {
    course_id: 'macro-401',
    title: 'Kinh tế Vĩ mô & Chu kỳ Tiền tệ Toàn cầu',
    description: 'Hệ thống hoá cỗ máy kinh tế, chu kỳ nợ và chính sách tiền tệ toàn cầu.',
    instructor: 'Ray Dalio • Prof. Robert Shiller',
    category: 'analysis',
    difficulty: 'Trung bình',
    total_duration: '1,5 giờ',
    lesson_count: 5,
    thumbnail_image: ytThumb('PHe0bXAIuk0'),
    sections: [
      sec('macro-s1', 'Cơ chế Vận hành Kinh tế & Lạm phát', [
        l('macro-l1', 'Máy kinh tế vận hành thế nào (Ray Dalio)', '31 phút', 'PHe0bXAIuk0'),
        l('macro-l2', 'Lạm phát, sức mua và thước đo CPI (Khan)', '8 phút', 'AaR1mPrdbTc'),
        l('macro-l3', 'Lãi suất & Giá trị tiền tệ (Khan)', '8 phút', 'Rm6UdfRs3gw'),
      ]),
      sec('macro-s2', 'Tiền tệ, Khủng hoảng & Chu kỳ Nợ', [
        l('macro-l4', 'Khủng hoảng tư bản & bong bóng tài sản (RSA)', '11 phút', 'qOP2V_np2c0'),
        l('macro-l5', 'Chu kỳ nợ ngắn hạn và dài hạn (Ray Dalio)', '31 phút', 'XggDwAftez4'),
      ]),
    ],
  },
  {
    course_id: 'bctc-301',
    title: 'Đọc hiểu & Bóc tách Báo cáo Tài chính',
    description: 'BCTC cơ bản, bóc tách doanh thu và tư duy tài chính từ góc nhìn nhà đầu tư thực chiến.',
    instructor: 'ĐH Ngoại thương (FTU) • Vietstock',
    category: 'analysis',
    difficulty: 'Trung bình',
    total_duration: '2 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('Fi1wkUczuyk'),
    sections: [
      sec('bctc-s1', 'Đọc hiểu Bộ 3 Báo cáo Tài chính', [
        l('bctc-l1', 'Giải mã Bảng CĐKT, KQKD & Lưu chuyển tiền tệ', '45 phút', 'Fi1wkUczuyk'),
        l('bctc-l2', 'Tỷ số tài chính: Thanh khoản & Đòn bẩy (Wharton)', '12 phút', 'UcAY6qRHlw0'),
      ]),
      sec('bctc-s2', 'Bóc tách Dòng tiền & Bút toán Ảo', [
        l('bctc-l3', 'Phân tích Dòng tiền hoạt động kinh doanh', '47 phút', 'WEDIj9JBTC8'),
        l('bctc-l4', 'Nhận diện dấu hiệu bóp méo & Bút toán ảo', '25 phút', 'Fi1wkUczuyk'),
      ]),
    ],
  },
  {
    course_id: 'val-201',
    title: 'Định giá Doanh nghiệp & Đầu tư Giá trị',
    description: 'Mô hình chiết khấu DCF, định giá bội số P/E, P/B và triết lý biên an toàn Benjamin Graham.',
    instructor: 'Prof. Aswath Damodaran • Bill Ackman',
    category: 'investing',
    difficulty: 'Nâng cao',
    total_duration: '2,5 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('WEDIj9JBTC8'),
    sections: [
      sec('val-s1', 'Mô hình Định giá Chiết khấu & Bội số', [
        l('val-l1', 'Nguyên lý Chiết khấu dòng tiền DCF (Damodaran)', '45 phút', 'Fi1wkUczuyk'),
        l('val-l2', 'Định giá bội số tương đối & Chi phí vốn WACC', '47 phút', 'WEDIj9JBTC8'),
      ]),
      sec('val-s2', 'Triết lý Đầu tư Giá trị & Thẩm định Dự án', [
        l('val-l3', 'Nền tảng Tài chính & Triết lý Đầu tư Giá trị', '45 phút', 'CMQLdJa64Wk'),
        l('val-l4', 'Thẩm định Dự án Đầu tư & Phân bổ Nguồn vốn', '12 phút', 'UcAY6qRHlw0'),
      ]),
    ],
  },
  {
    course_id: 'inv-101',
    title: 'Thị trường Chứng khoán & Kỹ thuật Giao dịch',
    description: 'Cơ chế vận hành thị trường chứng khoán, quy chế khớp lệnh, chọn lọc cổ phiếu và tâm lý.',
    instructor: 'NEU • SSI Academy • Netflix Explained',
    category: 'investing',
    difficulty: 'Cơ bản',
    total_duration: '1 giờ',
    lesson_count: 5,
    thumbnail_image: ytThumb('ZCFkWDdmXG8'),
    sections: [
      sec('vnstock-s1', 'Cơ chế Vận hành & Khớp lệnh', [
        l('vnstock-l1', 'Bản chất & Cơ chế thị trường (Netflix)', '19 phút', 'ZCFkWDdmXG8'),
        l('vnstock-l2', 'Thị trường hoạt động ra sao & Cơ chế khớp lệnh', '5 phút', 'p7HKvqRI_Bo'),
        l('vnstock-l3', 'Phương pháp lọc & Chọn cổ phiếu tiềm năng', '5 phút', 'CMQLdJa64Wk'),
      ]),
      sec('vnstock-s2', 'Công cụ Đầu tư & Quản trị Tâm lý', [
        l('vnstock-l4', 'Quỹ đầu tư chỉ số ETF & Chiến lược tích sản', '12 phút', '5A4lp_oZ5zg'),
        l('vnstock-l5', 'Kinh tế học hành vi & Kỷ luật cắt lỗ trong đầu tư', '10 phút', 'dqxQ3E1bubI'),
      ]),
    ],
  },
  {
    course_id: 'quant-501',
    title: 'Quản trị Rủi ro Danh mục & Tài chính Định lượng',
    description: 'Lý thuyết Markowitz, Factor Investing, Machine Learning tài chính và kiểm soát biến động.',
    instructor: 'Stanford Online • Ben Felix • QuantVN Lab',
    category: 'tools',
    difficulty: 'Nâng cao',
    total_duration: '1,5 giờ',
    lesson_count: 4,
    thumbnail_image: ytThumb('1FXuMs6YRCY'),
    sections: [
      sec('quant-s1', 'Lý thuyết Danh mục & Factor Investing', [
        l('quant-l1', 'Đa dạng hoá danh mục quốc tế (Ben Felix)', '12 phút', '1FXuMs6YRCY'),
        l('quant-l2', 'Factor Investing với các quỹ ETF nhân tố', '14 phút', 'jKWbW7Wgm0w'),
      ]),
      sec('quant-s2', 'Machine Learning & Mô phỏng Rủi ro', [
        l('quant-l3', 'Machine Learning & Time Series cho tài chính', '45 phút', 'psOYFdx838E'),
        l('quant-l4', 'Mô phỏng Monte Carlo & Quản trị rủi ro VaR', '20 phút', 'psOYFdx838E'),
      ]),
    ],
  },
]
