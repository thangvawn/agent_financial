# Bảng Mô tả Use Case Chi tiết (Use Case Specifications)

---

## UC-M5.4: Xử lý Phạt Giáo dục và Mở khóa Tài khoản

| Thuộc tính | Chi tiết |
| --- | --- |
| **UC ID** | UC-M5.4 |
| **Tên** | Xử lý Phạt Giáo dục và Mở khóa Tài khoản |
| **Actor** | Sinh viên, Hệ thống |
| **Điều kiện trước** | Account locked (PnL < -50% HOẶC 3 stop-loss violations liên tiếp) |
| **Luồng chính** | 1. Sinh viên thấy thông báo 'Account Locked' trên Dashboard.<br>2. Sinh viên nhấn nút 'Học để mở khóa'.<br>3. Hệ thống chuyển hướng sinh viên sang Learn Hub.<br>4. Sinh viên bắt đầu làm bài Quiz Quản trị Rủi ro (QTRR).<br>5. Hệ thống chấm điểm bài Quiz.<br>6. Hệ thống thực hiện mở khóa (Unlock/Retry) dựa trên điểm số. |
| **Luồng thay thế** | Nếu điểm < 80%: Hệ thống không mở khóa và yêu cầu sinh viên phải làm lại bài Quiz. |
| **Điều kiện sau** | Account active, virtual capital được phục hồi, learning progress (tiến độ học tập) được cập nhật. |
| **Quy tắc nghiệp vụ** | - Điểm pass phải >= 80%.<br>- Tối đa 3 lần mở khóa/tháng. Từ lần thứ 4 trở đi yêu cầu liên hệ Admin/Instructor.<br>- Ghi log sự kiện 'Account Unlocked via Education'. |
| **Ghi chú** | Đây là cơ chế cốt lõi thể hiện triết lý "Learn Hub là gốc". |

> [!CAUTION]
> Sinh viên vi phạm lần 4 trong tháng sẽ không thể tự động mở khóa thông qua Quiz mà phải chờ Admin phê duyệt.

---

## UC-M2.3: Làm bài Quiz và Mở khóa Tính năng

| Thuộc tính | Chi tiết |
| --- | --- |
| **UC ID** | UC-M2.3 |
| **Tên** | Làm bài Quiz và Mở khóa Tính năng |
| **Actor** | Sinh viên, Hệ thống |
| **Điều kiện trước** | Sinh viên đã hoàn thành (completed) một chương học tương ứng trong Learn Hub. |
| **Luồng chính** | 1. Sinh viên bắt đầu bài Quiz.<br>2. Sinh viên trả lời các câu hỏi trắc nghiệm.<br>3. Sinh viên nộp bài (submit).<br>4. Hệ thống chấm điểm, nếu score >= 80%.<br>5. Hệ thống mở khóa các tính năng nâng cao (Backtest, Deep BCTC). |
| **Luồng thay thế** | Nếu score < 80%: Hệ thống giữ nguyên trạng thái khóa và gợi ý sinh viên ôn tập lại bài học, sau đó có thể thử lại. |
| **Điều kiện sau** | Tính năng khóa trước đó được mở, thông báo chúc mừng hiển thị. |
| **Quy tắc nghiệp vụ** | - Mỗi bài Quiz có 10 câu hỏi.<br>- Giới hạn thời gian: 15 phút.<br>- Cho phép retry (làm lại) không giới hạn số lần. |
| **Ghi chú** | Cơ chế gamification giúp sinh viên có động lực hoàn thành bài học. |

> [!IMPORTANT]
> Việc mở khóa tính năng nâng cao ở các Module khác (M3, M5) phụ thuộc hoàn toàn vào bài kiểm tra này.

---

## UC-M4.3: Tương tác Ticker Tag

| Thuộc tính | Chi tiết |
| --- | --- |
| **UC ID** | UC-M4.3 |
| **Tên** | Tương tác Ticker Tag |
| **Actor** | Sinh viên |
| **Điều kiện trước** | Sinh viên đang đọc một bài báo/tin tức (M4) có chứa các ticker tags (ví dụ: MWG, FPT). |
| **Luồng chính** | 1. Sinh viên click chuột (hoặc tap) vào một ticker tag.<br>2. Hệ thống hiển thị popup nhanh chứa thông tin giá cổ phiếu.<br>3. Sinh viên có tùy chọn bấm nút chuyển hướng sang trang Phân tích BCTC (M3) của mã đó. |
| **Luồng thay thế** | Nếu kết nối dữ liệu bị lỗi, popup sẽ hiển thị thông báo "Dữ liệu đang được cập nhật". |
| **Điều kiện sau** | Sinh viên được chuyển hướng sang Module 3 hoặc đóng popup và tiếp tục đọc tin tức. |
| **Quy tắc nghiệp vụ** | - Hiển thị giá real-time nếu có sẵn dữ liệu và trong phiên giao dịch.<br>- Nếu không có dữ liệu real-time, hiển thị giá EOD (End Of Day) kèm theo timestamp. |
| **Ghi chú** | Nâng cao tính tương tác liên kết giữa Tin tức và Phân tích cơ bản. |
