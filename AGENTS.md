<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->

## Northstar: thực hiện và bàn giao

- Bắt đầu từ `docs/project/memory/INDEX.md`; chỉ đọc hồ sơ liên quan và kiểm tra lại source hiện tại.
- Dùng [quy trình làm việc](docs/project/engineering/WORKFLOW.md). Tác vụ lớn có yêu cầu, tiêu chí nghiệm thu và các đầu việc nhỏ; sửa đơn giản đi thẳng vào thay đổi và kiểm chứng.
- [Backlog](docs/project/engineering/BACKLOG.md) phân biệt `proposed`, `ready`, `in_progress`, `done`. Đề xuất chưa được chấp thuận không tự trở thành yêu cầu triển khai.
- Mỗi đầu việc phải cho kết quả quan sát được từ giao diện hoặc API/lệnh công khai. Kiểm thử hành vi; tránh kiểm thử chỉ đọc source hoặc mô phỏng lại cách implementation tính kết quả.
- Backend test: dùng `.venv/bin/python scripts/qa/run_isolated_tests.py -- <test paths>` để đặt DB tạm trước import. Đọc test trước khi mở rộng phạm vi: lệnh này không chặn đường dẫn ghi cứng hay truy cập mạng.
- Frontend: chọn test phù hợp; chạy lint/CSS/build khi thay đổi liên quan. UI cần dùng thử và xem kết quả trong trình duyệt.
- Bàn giao kèm phạm vi kiểm chứng, lỗi/giới hạn còn lại và liên kết bằng chứng. Không suy ra toàn dự án đã đạt từ một nhóm test.
- Giữ nguyên công việc/staging sẵn có. Không tự push, publish hoặc deploy. Không dùng `sites`/`visualize` trừ khi người dùng yêu cầu đích danh.
- Nếu `codegraph explore` không được CLI hỗ trợ, dùng `python3 scripts/codegraph_explore.py <symbol>`; đối chiếu với source vì index có thể cũ.
