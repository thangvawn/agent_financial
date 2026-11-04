# WF — Vòng kiểm chứng đáng tin cho Northstar

Ngày: 31/10/2026. Trạng thái: **completed trên workspace**. CI remote chưa chạy.
Nguồn: người dùng yêu cầu áp dụng các nguyên tắc workshop AI Coding vào dự án.

## Vấn đề

`frontend/scripts/test-runner.mjs` trả exit 0 khi không tìm thấy test và bỏ qua option sai. `.github/workflows/ci.yml` mới chạy frontend lint/build. Backend có test import ứng dụng trước fixture; DB mặc định có thể được chọn ngay lúc import. Sự cố reset DB trước đây được ghi tại [memory](../../memory/sessions/2026-10-31-book-source-audit.md).

## Kết quả cần có

Người phát triển có thể chạy một nhóm test, nhận kết quả lỗi đúng và bằng chứng xem lại; test backend dùng cấu hình runtime tạm ngay trước khi ứng dụng được import.

| ID | Tiêu chí nghiệm thu |
| --- | --- |
| AC1 | Frontend: không tìm thấy test → exit 1; tham số sai/thiếu → exit 2; giữ hành vi pass/fail và hai cách truyền filter |
| AC2 | Backend CLI: DB được tạo lúc import và fixture pytest nằm trong vùng tạm; DB đối chứng được truyền từ môi trường không đổi |
| AC3 | Backend CLI: giữ exit code của test lỗi/không có test; timeout trả 124 và dọn process/runtime; có log và JSON report |
| AC4 | CI cấu hình frontend unit/CSS và backend runner; giữ các bước lint/build hiện có |
| AC5 | Quy trình/task template/backlog có trạng thái, liên kết và hướng dẫn chạy thật |

## Quyết định triển khai

- Một lệnh Python stdlib gọi pytest trong process mới. Ba alias DB theo `platform/database/config.py` cùng trỏ DB tạm. Kệ sách lưu file bên cạnh DB nên cùng được cô lập.
- Kiểm thử CLI từ process bên ngoài bằng fixture dùng một lần; không gọi reset dữ liệu hiện hữu. Chứng minh pass, fail, empty collection và timeout.
- Giữ runner Node hiện có, sửa cách xử lý tham số và empty selection. Không thêm framework test mới.
- Đổi CI là thay đổi cấu hình local; pipeline remote chưa chạy cho tới khi người dùng đưa thay đổi lên remote.
- Runner không chặn mọi I/O hoặc provider; không tuyên bố thay thế container sandbox. Toàn bộ test backend cũ chưa mặc nhiên được chứng nhận an toàn/đạt.
- Ngoài phạm vi: khôi phục DB cũ, thay nghiệp vụ tài chính, xuất/in notebook, cài skill/agent loop toàn cục, push/deploy.

## Đầu việc và bằng chứng

Xem [WF-01 đến WF-04](../BACKLOG.md) và [kết quả kiểm chứng](../../memory/sessions/2026-10-31-ai-coding-workflow.md). Không lấy số test lịch sử làm kết quả của lượt này.
