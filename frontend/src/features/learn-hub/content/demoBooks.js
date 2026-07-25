/** Curated featured books — prefer live Archive.org PDFs + local sample. */

const LOCAL_SAMPLE = {
  book_id: 'b-local-sample',
  title: 'Northstar Sample Reader',
  original_title: 'Sample PDF (local)',
  author: 'Northstar Finance Lab',
  category: 'finance',
  pages: 1,
  read_time: '2 phút',
  rating: 5,
  cover_image: '',
  cover_color: 'linear-gradient(135deg, #0d9488 0%, #115e59 100%)',
  summary: 'File PDF mẫu local — luôn đọc được trong app để kiểm tra Reader Workspace.',
  url: '/learning-assets/books/northstar-sample-reader.pdf',
  download_url: '/learning-assets/books/northstar-sample-reader.pdf',
  pdf_url: '/learning-assets/books/northstar-sample-reader.pdf',
  file_name: 'northstar-sample-reader.pdf',
  key_takeaways: [
    'Đây là sách mẫu để xác nhận luồng Đọc trong app.',
    'Sách catalog lấy PDF từ Archive.org qua proxy backend.',
    'Nếu nguồn ngoài lỗi, dùng nút Nguồn để mở tab mới.',
  ],
}

export const DEMO_BOOKS = [
  LOCAL_SAMPLE,
  {
    book_id: 'b-wartime-finance',
    title: 'War-time Financial Problems',
    original_title: 'War-time financial problems',
    author: 'Hartley Withers',
    category: 'analysis',
    pages: 210,
    read_time: '3.5 giờ',
    rating: 4.5,
    cover_image: 'https://archive.org/services/img/WarTimeFinancialProblems',
    cover_color: 'linear-gradient(135deg, #8b5cf6 0%, #5b21b6 100%)',
    summary: 'Góc nhìn lịch sử về khủng hoảng tài chính — PDF công cộng qua proxy (~24MB, lần đầu hơi chậm).',
    url: 'https://archive.org/details/WarTimeFinancialProblems',
    download_url: 'https://archive.org/download/WarTimeFinancialProblems/WarTimeFinancialProblems.pdf',
    pdf_url: 'https://archive.org/download/WarTimeFinancialProblems/WarTimeFinancialProblems.pdf',
    file_name: 'WarTimeFinancialProblems.pdf',
    key_takeaways: [
      'Khủng hoảng tài chính thường lặp lại mẫu hình cũ.',
      'Tín dụng và niềm tin gắn chặt với chu kỳ kinh tế.',
      'Chính sách công có thể làm dịu hoặc làm sâu khủng hoảng.',
    ],
  },
]
