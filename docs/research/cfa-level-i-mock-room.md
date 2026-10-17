# CFA Level I mock room

## Phạm vi nội dung

Phòng thi trong Learn Hub hiện dùng một full session luyện tập của CFA® Level I. Bộ đề gồm 90 câu trắc nghiệm gốc, phủ 10 topic trong blueprint Level I 2027, mỗi câu có ba lựa chọn A/B/C, đáp án và lời giải sư phạm. Mỗi topic có chín câu để kết quả có thể chỉ ra topic yếu thay vì chỉ trả về một điểm tổng.

Đây là nội dung do Northstar biên soạn. Không tải, nhúng hoặc phát hành lại câu hỏi, đáp án hay curriculum có bản quyền của CFA Institute. Các liên kết chính thức trong lobby chỉ dẫn người học tới format Level I và sample questions công khai của CFA Institute.

## Đối chiếu format công khai

- CFA Institute mô tả Level I là 180 câu multiple-choice, chia thành hai session 135 phút; mỗi câu có ba lựa chọn và không trừ điểm khi đoán.
- Blueprint 2027 được dùng để đặt tên topic và dải trọng số: Ethical and Professional Standards, Quantitative Methods, Economics, Financial Statement Analysis, Corporate Issuers, Equity Investments, Fixed Income, Derivatives and Risk Management, Alternative Investments và Portfolio Construction.
- AlphaMock công khai một mock Level I session 90 câu trong 135 phút; trang chủ ghi nguồn đề tổng hợp từ CFA Institute, Kaplan Schweser và UWorld. Ứng dụng chỉ dùng format đó để tham khảo và liên kết sang AlphaMock, không sao chép ngân hàng câu hỏi.
- AlphaMock có link làm thử công khai, nhưng `robots.txt` của họ chặn `/api/` và `/exam/`; không dùng scraping hoặc gọi endpoint nội bộ để kéo ngân hàng câu hỏi vào hệ thống.
- Phiên trong ứng dụng là một full session: 90 câu trong 135 phút, khoảng 90 giây/câu. Hai session tương ứng với 180 câu của Level I đầy đủ.
- Mốc 70% trong ứng dụng là `benchmarkScore` phục vụ tự chẩn đoán; đây không phải MPS hoặc kết quả thi do CFA Institute công bố.

## Luồng trải nghiệm

1. Lobby hiển thị Level, năm blueprint, format chính thức, session 90 câu, topic và liên kết nguồn CFA/AlphaMock.
2. Cockpit có timer tính từ `startedAt`, tự lưu localStorage, navigator 90 câu, gắn cờ, highlight, gạch phương án, phím tắt và trạng thái responsive.
3. Người học chọn một trong hai chế độ: **Thi thử** giữ kín đáp án đến khi nộp; **Luyện tập** mở đáp án, giải thích và takeaway ngay sau khi chọn.
4. Nộp bài cảnh báo câu chưa trả lời; hết giờ tự nộp với cùng logic chấm.
5. Result hiển thị số câu đúng, thời gian, tỷ lệ theo topic yếu nhất và bộ lọc review theo tất cả, câu sai, chưa trả lời hoặc đã gắn cờ.

## Nguồn chính thức

- [CFA Level I exam structure and topic weights](https://www.cfainstitute.org/programs/cfa-program/candidate-resources/level-i-exam)
- [CFA Level I public sample questions](https://www.cfainstitute.org/programs/cfa-program/cfa-program-level-i-sample-questions)
- [CFA candidate resources and Learning Ecosystem](https://www.cfainstitute.org/programs/cfa-program/candidate-resources)

## Việc cần làm trước khi mở rộng production

Answer key hiện nằm trong bundle để demo có thể chạy offline. Khi triển khai cho kỳ thi có giám sát, cần chuyển question bank và grading sang API server, trả về question payload không có `correctOptionId`, lưu attempt theo user/session, audit version blueprint và giới hạn quyền xem lời giải sau khi submit.

## Khoảng cách so với blueprint production

Bản demo giữ chín câu cho mỗi topic để mỗi topic đều có mẫu đủ lớn cho mục tiêu tự chẩn đoán. Đây là lựa chọn sư phạm, không phải cam kết rằng phân bổ câu hỏi giống tỷ trọng thi thật. Bộ sinh đề production cần dùng dải trọng số theo blueprint tại thời điểm đăng ký thi, làm tròn tổng đúng 90 câu cho từng session, lưu snapshot blueprint cùng attempt và kiểm tra phân bổ trước khi cho nộp.
