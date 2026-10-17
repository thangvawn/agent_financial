"""Curated thematic course masterclasses combining global and Vietnamese sources."""
from __future__ import annotations

def _l(lid: str, title: str, dur: str, vid: str) -> dict:
    return {"lesson_id": lid, "title": title, "duration": dur, "video_id": vid, "video_url": f"https://www.youtube.com/watch?v={vid}"}

def _sec(sid: str, title: str, lessons: list[dict]) -> dict:
    return {"section_id": sid, "title": title, "lessons": lessons}

OPEN_COURSES: list[dict] = [
    {
        "code": "macro-401", "title": "Kinh tế Vĩ mô & Chu kỳ Tiền tệ Toàn cầu",
        "provider": "Yale • Bridgewater • Columbia / INET", "instructor": "Ray Dalio • Robert Shiller",
        "topics": ["macroeconomics", "inflation", "banking_products"], "level": "intermediate", "duration_minutes": 89, "language": "vi",
        "url": "https://www.youtube.com/watch?v=PHe0bXAIuk0", "thumbnail_url": "https://img.youtube.com/vi/PHe0bXAIuk0/hqdefault.jpg",
        "description": "Hệ thống hoá cỗ máy kinh tế, chu kỳ nợ, chính sách tiền tệ và bài học từ các cuộc khủng hoảng tài chính toàn cầu.",
        "sections": [
            _sec("macro-s1", "Cơ chế Vận hành Kinh tế & Lạm phát", [
                _l("macro-l1", "Máy kinh tế vận hành thế nào (Ray Dalio)", "31 phút", "PHe0bXAIuk0"),
                _l("macro-l2", "Lạm phát, sức mua và thước đo CPI (Khan)", "8 phút", "AaR1mPrdbTc"),
                _l("macro-l3", "Lãi suất & Giá trị tiền tệ (Khan)", "8 phút", "Rm6UdfRs3gw"),
            ]),
            _sec("macro-s2", "Tiền tệ, Khủng hoảng & Chu kỳ Nợ", [
                _l("macro-l4", "Khủng hoảng tư bản & bong bóng tài sản (RSA)", "11 phút", "qOP2V_np2c0"),
                _l("macro-l5", "Chu kỳ nợ ngắn hạn và dài hạn thực tế (Dalio)", "31 phút", "XggDwAftez4"),
            ]),
        ],
    },
    {
        "code": "bctc-301", "title": "Đọc hiểu & Bóc tách Báo cáo Tài chính Thực chiến",
        "provider": "ĐH Ngoại thương (FTU) • Vietstock • Big Think", "instructor": "Khoa TC-NH FTU • Vietstock",
        "topics": ["financial_statements", "valuation", "vietnam_market"], "level": "intermediate", "duration_minutes": 109, "language": "vi",
        "url": "https://www.youtube.com/watch?v=Fi1wkUczuyk", "thumbnail_url": "https://img.youtube.com/vi/Fi1wkUczuyk/hqdefault.jpg",
        "description": "Phương pháp đọc hiểu Bảng CĐKT, KQKD, Lưu chuyển tiền tệ và kỹ thuật nhận diện thủ thuật làm đẹp số liệu BCTC.",
        "sections": [
            _sec("bctc-s1", "Đọc hiểu Bộ 3 Báo cáo Tài chính", [
                _l("bctc-l1", "Giải mã Bảng CĐKT, KQKD & Lưu chuyển tiền tệ", "45 phút", "Fi1wkUczuyk"),
                _l("bctc-l2", "Tỷ số tài chính: Thanh khoản & Đòn bẩy (Wharton)", "12 phút", "UcAY6qRHlw0"),
            ]),
            _sec("bctc-s2", "Bóc tách Dòng tiền & Thủ thuật BCTC", [
                _l("bctc-l3", "Phân tích Dòng tiền hoạt động kinh doanh", "47 phút", "WEDIj9JBTC8"),
                _l("bctc-l4", "Nhận diện dấu hiệu bóp méo & Bút toán ảo", "25 phút", "Fi1wkUczuyk"),
            ]),
        ],
    },
    {
        "code": "val-201", "title": "Định giá Doanh nghiệp & Đầu tư Giá trị",
        "provider": "NYU Stern • Columbia Business School", "instructor": "Prof. Aswath Damodaran • Bill Ackman",
        "topics": ["valuation", "stocks", "financial_statements"], "level": "advanced", "duration_minutes": 149, "language": "vi",
        "url": "https://www.youtube.com/watch?v=WEDIj9JBTC8", "thumbnail_url": "https://img.youtube.com/vi/WEDIj9JBTC8/hqdefault.jpg",
        "description": "Giáo trình định giá toàn diện của Aswath Damodaran: mô hình DCF, bội số P/E, P/B và triết lý biên an toàn Benjamin Graham.",
        "sections": [
            _sec("val-s1", "Mô hình Định giá Chiết khấu & Bội số", [
                _l("val-l1", "Nguyên lý Chiết khấu dòng tiền DCF (Damodaran)", "45 phút", "Fi1wkUczuyk"),
                _l("val-l2", "Định giá bội số tương đối & Chi phí vốn WACC", "47 phút", "WEDIj9JBTC8"),
            ]),
            _sec("val-s2", "Triết lý Đầu tư Giá trị & Thẩm định Dự án", [
                _l("val-l3", "Nền tảng Tài chính & Triết lý Đầu tư Giá trị", "45 phút", "CMQLdJa64Wk"),
                _l("val-l4", "Thẩm định Dự án Đầu tư & Phân bổ Nguồn vốn", "12 phút", "UcAY6qRHlw0"),
            ]),
        ],
    },
    {
        "code": "inv-101", "title": "Thị trường Chứng khoán & Kỹ thuật Giao dịch",
        "provider": "ĐH Kinh tế Quốc dân (NEU) • SSI Academy • Netflix", "instructor": "Viện NH-TC NEU • Plain Bagel",
        "topics": ["vietnam_market", "stocks", "technical_analysis"], "level": "beginner", "duration_minutes": 51, "language": "vi",
        "url": "https://www.youtube.com/watch?v=ZCFkWDdmXG8", "thumbnail_url": "https://img.youtube.com/vi/ZCFkWDdmXG8/hqdefault.jpg",
        "description": "Cơ chế vận hành thị trường chứng khoán, khớp lệnh sàn HOSE/HNX, chu kỳ T+2.5, tiêu chí lọc cổ phiếu và tâm lý.",
        "sections": [
            _sec("vnstock-s1", "Cơ chế Vận hành & Khớp lệnh", [
                _l("vnstock-l1", "Bản chất & Cơ chế thị trường (Netflix)", "19 phút", "ZCFkWDdmXG8"),
                _l("vnstock-l2", "Thị trường hoạt động ra sao & Cơ chế khớp lệnh", "5 phút", "p7HKvqRI_Bo"),
                _l("vnstock-l3", "Phương pháp lọc & Chọn cổ phiếu tiềm năng", "5 phút", "CMQLdJa64Wk"),
            ]),
            _sec("vnstock-s2", "Công cụ Đầu tư & Quản trị Tâm lý", [
                _l("vnstock-l4", "Quỹ đầu tư chỉ số ETF & Chiến lược tích sản", "12 phút", "5A4lp_oZ5zg"),
                _l("vnstock-l5", "Kinh tế học hành vi & Kỷ luật cắt lỗ trong đầu tư", "10 phút", "dqxQ3E1bubI"),
            ]),
        ],
    },
    {
        "code": "quant-501", "title": "Quản trị Rủi ro Danh mục & Tài chính Định lượng",
        "provider": "Stanford Online • Ben Felix • QuantVN Lab", "instructor": "Ben Felix • Stanford Research",
        "topics": ["portfolio_theory", "risk_management", "quantitative_finance"], "level": "advanced", "duration_minutes": 91, "language": "vi",
        "url": "https://www.youtube.com/watch?v=1FXuMs6YRCY", "thumbnail_url": "https://img.youtube.com/vi/1FXuMs6YRCY/hqdefault.jpg",
        "description": "Lý thuyết danh mục Markowitz, đầu tư theo nhân tố (Factor Investing), mô hình Machine Learning tài chính và kiểm soát rủi ro.",
        "sections": [
            _sec("quant-s1", "Lý thuyết Danh mục & Factor Investing", [
                _l("quant-l1", "Đa dạng hoá danh mục quốc tế (Ben Felix)", "12 phút", "1FXuMs6YRCY"),
                _l("quant-l2", "Factor Investing với các quỹ ETF nhân tố", "14 phút", "jKWbW7Wgm0w"),
            ]),
            _sec("quant-s2", "Machine Learning & Mô phỏng Rủi ro", [
                _l("quant-l3", "Machine Learning & Time Series cho tài chính", "45 phút", "psOYFdx838E"),
                _l("quant-l4", "Mô phỏng Monte Carlo & Quản trị rủi ro VaR", "20 phút", "psOYFdx838E"),
            ]),
        ],
    },
    {
        "code": "bond-601", "title": "Thị trường Trái phiếu & Đường cong Lợi suất",
        "provider": "Wharton School • Khan Academy", "instructor": "Prof. Michael Roberts • Sal Khan",
        "topics": ["bonds", "time_value_of_money", "banking_products"], "level": "intermediate", "duration_minutes": 65, "language": "vi",
        "url": "https://www.youtube.com/watch?v=Qh-M3_L4xYk", "thumbnail_url": "https://img.youtube.com/vi/Qh-M3_L4xYk/hqdefault.jpg",
        "description": "Bản chất thị trường thu nhập cố định, định giá trái phiếu, mối quan hệ nghịch đảo giữa giá và lãi suất, đường cong lợi suất.",
        "sections": [
            _sec("bond-s1", "Bản chất & Định giá Trái phiếu", [
                _l("bond-l1", "Khái niệm & Cơ chế vận hành Trái phiếu (Khan)", "15 phút", "Qh-M3_L4xYk"),
                _l("bond-l2", "Mối quan hệ giữa Giá trái phiếu và Lãi suất", "12 phút", "vAdn7aLHpO0"),
            ]),
            _sec("bond-s2", "Đường cong Lợi suất & Định giá Dòng tiền", [
                _l("bond-l3", "Đường cong lợi suất Yield Curve & Tín hiệu vĩ mô", "18 phút", "b_cAxh44aNQ"),
                _l("bond-l4", "Giá trị thời gian của tiền & Chiết khấu (Wharton)", "20 phút", "UcAY6qRHlw0"),
            ]),
        ],
    },
    {
        "code": "deriv-701", "title": "Thị trường Phái sinh & Chiến lược Quyền chọn",
        "provider": "Khan Academy • InTheMoney Derivatives Lab", "instructor": "Sal Khan • Derivatives Specialist",
        "topics": ["derivatives", "risk_management", "quantitative_finance"], "level": "advanced", "duration_minutes": 70, "language": "vi",
        "url": "https://www.youtube.com/watch?v=7PM4rNDr4oI", "thumbnail_url": "https://img.youtube.com/vi/7PM4rNDr4oI/hqdefault.jpg",
        "description": "Hợp đồng quyền chọn (Options) mua và bán, đồ thị hoàn trả Payoff Diagrams, chiến lược phòng hộ rủi ro và đầu cơ thông minh.",
        "sections": [
            _sec("deriv-s1", "Căn bản Quyền chọn & Hợp đồng Phái sinh", [
                _l("deriv-l1", "Nhập môn Giao dịch Quyền chọn Options", "25 phút", "7PM4rNDr4oI"),
                _l("deriv-l2", "Hợp đồng Quyền chọn Mua - Call Options (Khan)", "15 phút", "nnl3x1wo25g"),
            ]),
            _sec("deriv-s2", "Quyền chọn Bán & Chiến lược Phòng hộ", [
                _l("deriv-l3", "Hợp đồng Quyền chọn Bán - Put Options (Khan)", "15 phút", "6CUcgUeQS-w"),
                _l("deriv-l4", "Chiến lược Phòng hộ Hedging & Payoff Diagrams", "15 phút", "WFuLVSz6n8M"),
            ]),
        ],
    },
    {
        "code": "fintech-801", "title": "Công nghệ FinTech, Blockchain & Web3 Finance",
        "provider": "MIT OpenCourseWare • 3Blue1Brown", "instructor": "Prof. Gary Gensler (MIT) • Grant Sanderson",
        "topics": ["banking_products", "quantitative_finance"], "level": "intermediate", "duration_minutes": 82, "language": "vi",
        "url": "https://www.youtube.com/watch?v=5auv_xrvoJk", "thumbnail_url": "https://img.youtube.com/vi/5auv_xrvoJk/hqdefault.jpg",
        "description": "Bản chất của tiền tệ, sổ cái phân tán, công nghệ blockchain, hàm băm mật mã học và tương lai của thanh toán phi tập trung.",
        "sections": [
            _sec("fintech-s1", "Kiến trúc Tiền tệ & Blockchain Nền tảng", [
                _l("fintech-l1", "Blockchain và Bản chất Tiền tệ (Gary Gensler)", "35 phút", "5auv_xrvoJk"),
                _l("fintech-l2", "Bản chất Thuật toán Bitcoin & Sổ cái Phân tán", "25 phút", "bBC-nXj3Ng4"),
            ]),
            _sec("fintech-s2", "Mật mã học & Tài chính Phi tập trung", [
                _l("fintech-l3", "Hàm băm Mật mã học & Bảo mật Giao dịch", "12 phút", "SSo_EIwHSd4"),
                _l("fintech-l4", "Hợp đồng Thông minh & Cơ chế Đồng thuận (MIT)", "10 phút", "5auv_xrvoJk"),
            ]),
        ],
    },
    {
        "code": "psych-901", "title": "Tâm lý học Hành vi & Kỷ luật Giao dịch",
        "provider": "Crash Course • TED-Ed • Two Cents", "instructor": "Daniel Kahneman Research • Crash Course",
        "topics": ["behavioral_finance", "risk_management"], "level": "intermediate", "duration_minutes": 45, "language": "vi",
        "url": "https://www.youtube.com/watch?v=dqxQ3E1bubI", "thumbnail_url": "https://img.youtube.com/vi/dqxQ3E1bubI/hqdefault.jpg",
        "description": "Giải mã thiên kiến nhận thức, tâm lý sợ mất mát (loss aversion), bẫy chi phí chìm và cách xây dựng kỷ luật giao dịch.",
        "sections": [
            _sec("psych-s1", "Thiên kiến Nhận thức & Kinh tế học Hành vi", [
                _l("psych-l1", "Kinh tế học Hành vi & Tâm lý Ra quyết định", "10 phút", "dqxQ3E1bubI"),
                _l("psych-l2", "Thiên kiến Tránh lỗ & Chiến lược Trung bình giá", "8 phút", "vLTdlN7VJTM"),
            ]),
            _sec("psych-s2", "Tâm lý Đám đông & Kỷ luật Giao dịch", [
                _l("psych-l3", "Tâm lý Đám đông trong Khủng hoảng & Bong bóng", "11 phút", "qOP2V_np2c0"),
                _l("psych-l4", "Kiểm soát Cảm xúc & Kỷ luật Cắt lỗ Thực chiến", "5 phút", "CMQLdJa64Wk"),
            ]),
        ],
    },
    {
        "code": "wealth-1001", "title": "Quản lý Tài chính Cá nhân & Tích sản Thông minh",
        "provider": "Khan Academy • Plain Bagel • Ben Felix", "instructor": "Sal Khan • Ben Felix (PWL Capital)",
        "topics": ["saving", "portfolio_theory", "time_value_of_money"], "level": "beginner", "duration_minutes": 42, "language": "vi",
        "url": "https://www.youtube.com/watch?v=79HS3N1IBt8", "thumbnail_url": "https://img.youtube.com/vi/79HS3N1IBt8/hqdefault.jpg",
        "description": "Nền tảng tài chính cá nhân, sức mạnh của lãi kép, phân bổ tài sản đa lớp và chiến lược đầu tư tích sản thụ động dài hạn.",
        "sections": [
            _sec("wealth-s1", "Sức mạnh Lãi kép & Giá trị Tiền tệ", [
                _l("wealth-l1", "Tính toán Lãi đơn & Lãi kép thực tế (Khan)", "6 phút", "79HS3N1IBt8"),
                _l("wealth-l2", "Lãi suất & Giá trị Thời gian của Tiền (Khan)", "8 phút", "Rm6UdfRs3gw"),
            ]),
            _sec("wealth-s2", "Chiến lược Tích sản & Quản lý Danh mục", [
                _l("wealth-l3", "Quỹ Mở vs Quỹ Hoán đổi Danh mục ETF", "10 phút", "HghsQN89w9k"),
                _l("wealth-l4", "Xây dựng Danh mục Tài sản Đa tầng Bền vững", "12 phút", "1FXuMs6YRCY"),
            ]),
        ],
    },
]
