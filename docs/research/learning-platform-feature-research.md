# Nghiên cứu chức năng phù hợp cho nền tảng học tài chính

## 1. Định hướng sản phẩm

Northstar nên được định vị là một **learning loop** khép kín cho sinh viên tài chính và người học CFA:

`học khái niệm → thực hành trên dữ liệu/case → kiểm tra năng lực → nhận phản hồi → ôn đúng lỗ hổng → kiểm tra lại`

Learn Hub hiện đã có catalog khóa học, reader, video learning agent, AI tutor và CFA practice room. Chức năng cần ưu tiên tiếp theo không phải là thêm nhiều màn hình, mà là nối các module này thành một hồ sơ tiến bộ duy nhất theo topic và learning outcome.

## 2. Căn cứ nghiên cứu

- CFA Institute mô tả Level I là 180 câu multiple choice, hai session 135 phút, mỗi câu có ba lựa chọn và không trừ điểm khi đoán. Trang chính thức cũng công bố các topic và dải trọng số blueprint.
- AlphaMock công khai một mock Level I theo session gồm 90 câu trong 135 phút và cho phép chọn xem đáp án sau toàn bài hoặc sau từng câu. Đây là tham chiếu tốt cho **hành vi sản phẩm**, không phải nguồn để sao chép đề.
- CFA Institute nhấn mạnh Learning Ecosystem gồm curriculum số, practice questions, mock exams và study tools; vì vậy phòng thi nên là một phần của lộ trình học, không phải một trang tách rời.

Nguồn:

- [CFA Level I exam structure and topic weights](https://www.cfainstitute.org/programs/cfa-program/candidate-resources/level-i-exam)
- [CFA Level I public sample questions](https://www.cfainstitute.org/programs/cfa-program/cfa-program-level-i-sample-questions)
- [CFA candidate resources and Learning Ecosystem](https://www.cfainstitute.org/programs/cfa-program/candidate-resources)
- [AlphaMock](https://alphamock.com/)

## 3. Những chức năng phù hợp và thứ tự ưu tiên

| Ưu tiên | Chức năng | Giá trị học tập | Trạng thái |
| --- | --- | --- | --- |
| P0 | Full-session mock 90 câu/135 phút, navigator, timer, autosave, flag, eliminate | Rèn nhịp thi và khả năng phân bổ thời gian | Đã có |
| P0 | Hai mode Thi thử/Luyện tập | Tách đánh giá thật khỏi việc học có hướng dẫn | Đã triển khai |
| P0 | Chấm theo topic và review filter câu sai/chưa trả lời/gắn cờ | Biến điểm số thành danh sách hành động | Đã triển khai |
| P0 | Kho câu hỏi bản quyền rõ ràng, có explanation/takeaway | Tránh phụ thuộc dữ liệu không được cấp phép | Demo đang dùng câu tự biên soạn |
| P0 | Grading và answer key ở server | Không để người học xem đáp án qua bundle; chống gian lận khi mở rộng | Cần triển khai trước production |
| P1 | Topic practice và timed sprint 10–20 câu | Ôn một lỗ hổng nhỏ thay vì luôn làm cả 90 câu | Nên làm tiếp |
| P1 | Study plan theo kỳ thi, topic weight và thời gian rảnh | Chuyển benchmark thành lịch học thực tế | Nên làm tiếp |
| P1 | Review queue có spaced repetition | Đưa câu sai quay lại theo khoảng thời gian tăng dần | Nên làm tiếp |
| P1 | Formula sheet, calculator, glossary và worked example | Hỗ trợ các topic định lượng mà không rời trang | Nên làm tiếp |
| P1 | Mapping question → topic → learning outcome → lesson | Deep-link từ câu sai về đúng bài học | Nên làm tiếp |
| P1 | Progress dashboard: score trend, mastery, time/question, readiness | Theo dõi tiến bộ qua nhiều attempt | Nên làm tiếp |
| P2 | Case/vignette dài, nhiều câu liên tiếp | Tiệm cận dạng bài Level II sau khi nền tảng Level I ổn định | Sau P0/P1 |
| P2 | AI tutor grounded trên lesson, transcript và nguồn trích dẫn | Trả lời câu hỏi trong lúc học nhưng không bịa kiến thức | Sau khi có retrieval/evaluation |
| P2 | Cohort, discussion và instructor analytics | Hỗ trợ lớp học và giảng viên | Sau khi có privacy model |

## 4. Luồng người học nên thiết kế

### Bắt đầu

Người học chọn mục tiêu: “CFA Level I”, “nền tảng tài chính” hoặc “phân tích BCTC”. Hệ thống hỏi kỳ thi dự kiến, số giờ mỗi tuần và topic tự đánh giá. Nếu chưa có dữ liệu, tạo một diagnostic ngắn 10–20 câu trước khi lập kế hoạch.

### Học

Mỗi lesson nên có bốn lớp: mục tiêu đo được, video/đọc, worked example và checkpoint. Khi video kết thúc, agent có thể tạo câu hỏi nhận biết đơn giản; câu hỏi do AI tạo phải gắn transcript, timestamp và trạng thái “cần duyệt” trước khi đưa vào ngân hàng chính thức.

### Thực hành

- **Practice mode:** phản hồi ngay, giải thích ngắn, công thức nếu có, link về lesson.
- **Exam mode:** không lộ đáp án, timer 135 phút, cho phép flag/eliminate, chấm khi submit.
- **Topic mode:** chỉ lấy câu trong một topic, có giới hạn thời gian tuỳ chọn.
- **Sprint mode:** 10 câu ngẫu nhiên, 15 phút, dùng để duy trì thói quen hằng ngày.

### Sau bài

Kết quả phải trả lời ba câu hỏi: “Tôi đúng bao nhiêu?”, “Tôi yếu ở đâu?”, “Tôi làm gì tiếp theo?”. Vì vậy màn hình result cần có mastery theo topic, thời gian trung bình/câu, danh sách review và một CTA mở bài học liên quan. Benchmark 70% chỉ nên là mốc nội bộ; không gọi đó là pass mark hay MPS.

## 5. Mô hình dữ liệu đề xuất

```text
LearningPath
  └── Module
        └── Lesson (video | reading | case | quiz)
              └── LearningOutcome

QuestionBankItem
  id, version, blueprint_year, topic, learning_outcome_id,
  difficulty, stem, options, explanation, source_note, status

ExamBlueprint
  exam_id, level, year, session, duration_seconds,
  question_count, topic_weight_min, topic_weight_max

Attempt
  id, user_id, exam_id, blueprint_snapshot, mode,
  started_at, submitted_at, remaining_seconds, status

AttemptAnswer
  attempt_id, question_id, selected_option, flagged,
  elapsed_seconds, changed_count, is_correct (server-side)

MasteryEvent
  user_id, learning_outcome_id, attempt_id, result,
  confidence, next_review_at
```

`QuestionBankItem.version` và `ExamBlueprint` snapshot là bắt buộc. Khi blueprint thay đổi, attempt cũ vẫn phải tái hiện đúng cấu hình lúc làm bài.

## 6. API và bảo mật khi nâng từ demo lên production

1. `POST /learning/attempts` tạo attempt và trả về question payload đã loại `correctOptionId`.
2. `PATCH /learning/attempts/{id}/answers` lưu từng lựa chọn, flag và thời gian; endpoint phải idempotent.
3. `POST /learning/attempts/{id}/submit` khóa attempt phía server, tính điểm và trả về result snapshot.
4. `GET /learning/attempts/{id}/review` chỉ mở explanation theo policy của mode và trạng thái submit.
5. `GET /learning/mastery` trả về mastery theo topic/learning outcome để dùng cho dashboard và study plan.

Không đưa đáp án đúng, điểm server-side hoặc question bank đầy đủ vào JavaScript production. Cần rate limit, quyền truy cập theo user, audit log, chống sửa timer ở client và kiểm thử replay request. Chỉ sử dụng câu hỏi tự biên soạn hoặc nội dung đã có giấy phép; liên kết tới CFA/AlphaMock chỉ để tham khảo nguồn và format.

## 7. Chỉ số đánh giá

- Tỷ lệ hoàn thành lesson → checkpoint → practice.
- Tỷ lệ câu đúng lần đầu và lần review sau 24 giờ/7 ngày.
- Thời gian trung vị mỗi câu và tỷ lệ hết giờ.
- Tỷ lệ người học quay lại làm review queue.
- Độ cải thiện mastery theo topic sau hai attempt.
- Tỷ lệ câu hỏi AI tạo bị giảng viên sửa hoặc loại.
- Phân bố câu hỏi so với blueprint snapshot; không để topic bị thiếu mẫu.

## 8. Khoảng cách hiện tại và kế hoạch triển khai

Bản demo hiện ưu tiên đủ chín câu cho mỗi topic để chẩn đoán được cả mười topic. Điều này dễ hiểu với người học nhưng chưa phải bộ sinh đề theo dải trọng số production; cần thay bằng blueprint-weighted assembler trước khi gọi là mô phỏng sát kỳ thi. Answer key vẫn nằm trong frontend để chạy offline, nên chỉ phù hợp demo/local learning.

Lộ trình hợp lý:

1. Hoàn thiện P0: server-side attempt/grading, question versioning và topic-weighted assembly.
2. Xây P1: topic practice, sprint, study plan, review queue và lesson deep-link.
3. Thêm retrieval/evaluation cho AI tutor và video agent; không cho agent tự xuất bản câu hỏi chưa duyệt.
4. Chỉ sau khi có dữ liệu sử dụng ổn định mới mở rộng vignette, cohort và analytics cho giảng viên.
