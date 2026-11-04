# Mẫu yêu cầu, đầu việc và review

Ngày: 31/10/2026. Trạng thái: **accepted**. Dùng với [workflow](WORKFLOW.md); bỏ các phần không liên quan cho sửa nhỏ.

## Feature / PRD

```md
# <Kết quả người dùng cần>
Ngày: <YYYY-MM-DD>
Trạng thái: proposed | accepted | completed | superseded
Nguồn yêu cầu: <yêu cầu cụ thể / liên kết>

## Vấn đề và kết quả
Ai gặp vấn đề gì? Sau thay đổi họ làm được gì?

## Tiêu chí nghiệm thu
- AC1: Với <điều kiện>, khi <hành động>, thấy <kết quả>.
- AC2: Khi thất bại <tình huống>, dữ liệu và phản hồi phải <kết quả>.

## Phạm vi và quyết định
- Đã chấp thuận: ...
- Giả định kỹ thuật có thể đảo ngược: ...
- Chưa quyết định, cần người dùng: ...
- Ngoài phạm vi: ...

## Code và kiểm chứng
- Interface/UI/API chịu trách nhiệm: ...
- File/module cần đọc: ...
- Dữ liệu test tạm, provider fixture: ...
- Test có sẵn/chưa có; cách dùng thử: ...

## Đầu việc
Liên kết các task có dependencies và tiêu chí AC tương ứng.
```

## Task xuyên luồng

```md
# <ID> — <Một hành vi hoàn chỉnh>
Trạng thái: proposed | ready | in_progress | blocked | done
PRD/tiêu chí: <link, AC IDs>
Phụ thuộc: <task IDs hoặc không>
Phạm vi đã cho phép: <nguồn>

Đầu vào → hành động → kết quả quan sát được: ...
Interface và file cần đọc: ...
Dữ liệu test, tình huống lỗi và cách chạy: ...
Điều kiện hoàn tất: ...

Kết quả: <lệnh + exit code + artifact; ghi rõ chưa chạy>
Review: <đúng yêu cầu, dữ liệu, regression; ai/cách review>
Giới hạn: ...
```

## Gói review / bàn giao ngữ cảnh

```md
Yêu cầu hiện hành và phần đã được phép: ...
Task đang làm; việc còn lại: ...
Source/diff cần đọc; file bẩn có sẵn không thuộc task: ...
Tiêu chí nghiệm thu: ...
Lệnh đã chạy và bằng chứng: ...
Quyết định + lý do; giả định chưa kiểm chứng: ...
Các điểm cần soi: đúng hành vi, quyền sở hữu dữ liệu, lỗi/timeout,
giữ nội dung cũ, ranh giới module, test có quan sát được bug không.
Không cần đọc lại toàn bộ lịch sử chat; kiểm tra source thay vì tin báo cáo cũ.
```
