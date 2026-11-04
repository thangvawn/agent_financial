# Social — triển khai 02/11/2026

Status: **verified trên workspace và QA**; chưa deploy/rebuild/restart localhost:8000.

- **Accepted:** người dùng “oke triển khai” sau nghiên cứu Social riêng, phạm vi Việt Nam + quốc tế. S0/S1 và S2 mức trích đoạn có nguồn đã làm; X/Facebook, LLM/dịch và định lượng giữ điều kiện dữ liệu/nguồn ở giai đoạn sau.
- **Implemented:** `/dashboard-static/news/social`; filter market/platform/q/time/watchlist/saved, import URL, nguồn theo dõi, bài/revision/bookmark riêng owner; migration021. Worker bền, lease/fence/retry, source không chạy trong HTTP. Agent-Reach pinned `7a38047acf26a729cbb27851e3cb81639da86b29` trong `.venv-social-tools`; không login/cookie.
- **Verified:** 71 backend, 165 frontend (3 Social chạy lại sau sửa cuối), lint/CSS54/build riêng/Ruff/diff; 10 browser groups + 4 degraded-source groups, Chromium1440/768/390/320. DB/auth thật trong temp riêng. [Báo cáo](../../qa/results/SOCIAL_IMPLEMENTATION_2026_11_02.md).
- **Live:** 18 kết quả gồm12video VN/quốc tế và6Reddit; Reddit mẫu cũ, bị lọc khỏi7ngày. YouTube metadata đọc được nhưng phụ đề chưa thành công; lượt nhập lại RATE_LIMITED. Reddit read HTTP200 chứa trang chặn: đã sửa thành PLATFORM_BLOCKED, giữ cache, không bookmark nội dung lỗi. Không tuyên bố nguồn luôn khả dụng.
- **Current behavior:** tổng hợp chỉ bằng trích đoạn, stance unknown/attention unavailable; không có AI provider hoặc score được xác nhận. Instrument resolution bảo thủ, grouping title heuristics, chưa corpus đánh giá. [Vận hành/giới hạn](../../engineering/SOCIAL.md) là tài liệu hiện hành, [spec nghiên cứu](../../engineering/specs/social-intelligence.md) giữ lịch sử đề xuất rộng hơn.
- **Operations:** API auto-worker khi có collector; CLI worker riêng hỗ trợ DB chung. Docker base chưa đóng gói collector Linux, có thể chạy host worker cùng volume DB. Không mount Python macOS vào container. Không restart stack trong lượt này.
- CodeGraph đã thử trước source, CLI explore không có; fallback script repo dùng index cũ nên đối chiếu source. Impeccable review theo fallback trong lượt, không phải review độc lập; disposition ship cho UI đã thử.
- Không dùng DB thật để QA, không stage/commit/push; dữ liệu trước sự cố lịch sử không được khôi phục trong thay đổi này.
