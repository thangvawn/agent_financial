# Sửa lỗi dùng thử

**2026-10-31 · verified.** Người dùng yêu cầu sửa các lỗi đã review. Nguồn: [finding U01–U11](../../qa/results/USAGE_LOGIC_REVIEW_2026_10_31.md). Thay đổi, giới hạn dữ liệu cũ, kết quả/lệnh test và artifact: [báo cáo bàn giao](../../qa/results/USAGE_FIXES_2026_10_31.md).

Kiểm chứng gồm test hồi quy, API FastAPI thật trên DB tạm, Chromium desktop/mobile và tình huống font bị chặn. Không có deployment/push. RED checkpoint của lượt này là `fad05c0`; GREEN được tạo sau kiểm chứng. Các sửa nhỏ trên file đang có thay đổi của người dùng được giữ ngoài checkpoint, nên bằng chứng mô tả workspace, không phải checkout sạch riêng commit.
