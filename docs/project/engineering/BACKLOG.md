# Backlog áp dụng quy trình

Ngày: 31/10/2026. Chỉ mục đầu việc local, không đồng bộ issue bên ngoài.
`proposed` = đề xuất; `ready` = đủ yêu cầu/quyền thực hiện; `in_progress` = đang làm; `blocked` = cần gỡ phụ thuộc; `done` = có bằng chứng nghiệm thu.

## Dọn bản bàn giao — 04/11/2026

**done trong phạm vi cleanup**, theo yêu cầu người dùng. Đã loại mã không còn caller,
UI thay thế, script QA dùng một lần và output cũ; chặn dependency/cache/test artifact
trong Git/build. 180 frontend +128 backend +5 runner, lint/CSS/build/wheel và browser
đạt; giữ dữ liệu runtime, shim model pickle và chức năng hiện hành. Không push/deploy.
[Phạm vi, bằng chứng và giới hạn](../memory/sessions/2026-11-04-release-cleanup.md).

## Social — cập nhật 02/11/2026

- S0/S1 và S2 mức trích đoạn: **done trên workspace/QA**; [vận hành và scope](SOCIAL.md), [bằng chứng](../qa/results/SOCIAL_IMPLEMENTATION_2026_11_02.md).
- Dịch/LLM, nguồn kênh đầy đủ, X/Facebook và định lượng S3/S4: **proposed**, phụ thuộc capability/coverage/provider đã xác nhận; không tự mở bằng điểm giả trên search sample.

## Bộ lọc định lượng — cập nhật 01/11/2026

User đã yêu cầu áp dụng bộ lọc. [Đặc tả](specs/quant-stock-screener.md), [bằng chứng và giới hạn](../memory/sessions/2026-11-01-quant-screener-implementation.md).

| ID | Kết quả | Trạng thái |
| --- | --- | --- |
| QSC-01 | 12 quy tắc, kiểm tra dữ liệu, toàn-universe ranking, immutable snapshot, cursor API | done — fixture verified |
| QSC-02 | UI chọn preset, điểm/điều kiện, coverage/reasons, phân trang, requestrace | done — browser verified |
| QSC-03 | CLI bundle, cache riêng, collector có lock/checkpoint/backoff và session cutoff | done — contract verified; provider thật chưa thành công |
| QSC-04 | Lịch sử chuẩn toàn thị trường, benchmark tương thích, foreign/BCTC/events tự động | blocked — bản provider/quyền/schema hiện tại chưa đủ; có import bundle |
| QSC-05 | Backtest walk-forward, chi phí/độ ổn định và profile tài chính riêng | proposed — cần QSC-04 và thiết kế nghiên cứu riêng |

## Phạm vi đã hoàn tất trên workspace

PRD: [Vòng kiểm chứng đáng tin](specs/verification-feedback.md).

| ID | Luồng hoàn chỉnh | Phụ thuộc | AC | Trạng thái |
| --- | --- | --- | --- | --- |
| WF-01 | Gọi frontend test với bộ lọc sai → nhận lỗi đúng → sửa filter → chạy đúng test | Không | AC1 | done |
| WF-02 | Gọi backend test → app dùng DB tạm từ import → trả kết quả/log → dọn runtime | Không | AC2, AC3 | done |
| WF-03 | Cấu hình CI có frontend unit/CSS, backend runner và artifact log | WF-01, WF-02 | AC4 | done |
| WF-04 | Phiên làm việc tiếp theo tìm được yêu cầu, task, lệnh và bằng chứng | WF-01, WF-02 | AC5 | done |

Bằng chứng và lệnh chạy lại: [session kiểm chứng](../memory/sessions/2026-10-31-ai-coding-workflow.md). WF-03 nghiệm thu cấu hình và lệnh local; chưa chạy pipeline trên GitHub.

## Ví dụ chia việc tiếp theo — chưa triển khai

Các mục dưới là đề xuất minh họa từ phạm vi Learn Hub đang làm; cần chốt hành vi trước khi chuyển `ready`. Mỗi mục kết thúc bằng một kết quả người dùng có thể sử dụng.

| ID | Hành vi đề xuất | Phụ thuộc | Cách nghiệm thu dự kiến | Trạng thái |
| --- | --- | --- | --- | --- |
| LH-PRINT-01 | Từ sổ A4 mở bản in gồm chữ và tiêu đề, chọn in hoặc lưu PDF qua trình duyệt | Chốt luồng xuất/in | Đủ trang, tiếng Việt đúng, nội dung ghi chú gốc không đổi | proposed |
| LH-PRINT-02 | Bản in giữ ảnh/nét vẽ đúng trang và vị trí cùng nội dung chữ | LH-PRINT-01 | Sổ kết hợp chữ/ảnh/vẽ; đối chiếu preview/PDF với trang gốc | proposed |
| LH-SOURCE-01 | Khi nguồn PDF hỏng, user kiểm tra lại và thấy kết quả mới có thời điểm rõ | Chốt nhu cầu refresh so với hành vi hiện có | 404, timeout, nguồn phục hồi; không thay PDF bằng ghi chú | proposed |

Chưa chia kiểu “xây DB toàn bộ → xây API toàn bộ → xây UI toàn bộ”. Không triển khai các đề xuất này như phần ngầm của yêu cầu áp dụng workflow.
