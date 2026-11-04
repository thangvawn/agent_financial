# Quy trình phát triển Northstar với AI

Ngày: 31/10/2026. Trạng thái: **accepted** trong phạm vi yêu cầu áp dụng của người dùng.

## Cơ sở

Đã đọc bản chép lời của [workshop Matt Pocock](https://www.youtube.com/watch?v=-QFHIoCo-Ko&t=344s),
qua [bản transcript có timestamp](https://mwolf.dev/library/full-walkthrough-workflow-for-ai-coding-matt-pocock/full-walkthrough-workflow-for-ai-coding-matt-pocock),
và đối chiếu [repo chính chủ](https://github.com/mattpocock/skills).
Không truy xuất được phụ đề trực tiếp từ YouTube; đây là đối chiếu transcript/tài liệu, không phải kiểm chứng toàn bộ hình ảnh trình diễn.

| Mốc video | Ý chính | Cách dùng tại Northstar |
| --- | --- | --- |
| 05:44–10:40 | Việc nhỏ; ngữ cảnh ngắn, có thể khởi động lại | Mỗi lượt lấy một task cùng source và bằng chứng cần thiết |
| 12:12–21:09 | Làm rõ cách hiểu trước khi xây | Tận dụng lịch sử yêu cầu; chỉ hỏi quyết định chưa rõ |
| 28:37–34:40 | PRD ghi đích đến | Viết tiêu chí nghiệm thu quan sát được |
| 39:38–44:28 | Chia việc thành luồng chức năng xuyên các lớp cần thiết | Một task kết thúc bằng hành vi dùng được |
| 59:22–1:10:32 | QA, review, phản hồi từ test | Chạy ca lỗi → sửa → kiểm chứng; UI cần xem thực tế |
| 1:16:57–1:24:50 | Interface gọn; tránh tài liệu lỗi thời | Kiểm thử qua interface; đánh dấu tài liệu đã hoàn tất |

Các mốc token được diễn giả nêu là kinh nghiệm cá nhân, không dùng làm ngưỡng bắt buộc cho mọi model.
Repo của tác giả hiện đã đổi tên/mở rộng một số skill so với video. Tài liệu bên ngoài là nguồn tham khảo; quy tắc người dùng và code dự án quyết định cách áp dụng.

## Một vòng thực hiện

1. **Hiểu yêu cầu.** Đọc memory index, source liên quan và trạng thái Git. Ghi kết quả người dùng cần, điều kiện nghiệm thu, điều gì còn chưa rõ. Câu hỏi có thể giải đáp từ code thì tự kiểm tra. Nếu chỉ là sửa nhỏ, không cần tạo đủ bộ tài liệu.
2. **Chốt phạm vi.** Dùng [mẫu feature/task](TEMPLATES.md) cho việc lớn. Phân biệt yêu cầu đã chấp thuận và đề xuất. Chỉ hỏi người dùng về quyết định ảnh hưởng hành vi/nghiệp vụ còn thiếu; các lựa chọn kỹ thuật thông thường do agent xử lý.
3. **Chọn một task sẵn sàng.** Xem [backlog](BACKLOG.md), chọn việc có đầu ra và không còn phụ thuộc chưa xong. Một task có thể chạm UI, API và storage nếu cùng phục vụ một hành vi. Tránh chia thành “làm hết DB”, rồi “làm hết API”, rồi mới dùng thử.
4. **Thực hiện với phản hồi ngắn.** Với logic quan trọng hoặc bug, tái hiện lỗi trước, sửa tối thiểu rồi kiểm tra lại. Với điều chỉnh giao diện nhỏ, dùng kiểm tra có sẵn và trình duyệt; không thêm test chỉ để đếm coverage. Ưu tiên test qua API, UI hoặc CLI như người gọi thực tế. Xem [hướng dẫn TDD chính chủ](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md) như tài liệu kỹ thuật tham khảo.
5. **Review theo hai câu hỏi.** Kết quả có đúng yêu cầu không? Code có đúng ranh giới module và làm mất dữ liệu/hành vi cũ không? Chuẩn bị diff, tiêu chí và log để có thể review trong ngữ cảnh mới; không coi self-review là review độc lập. Chỉ dùng agent bổ sung khi phiên làm việc cho phép.
6. **Đóng task.** Ghi lệnh, kết quả, giới hạn, đường dẫn artifact. `done` chỉ khi tiêu chí đạt; lỗi hạ tầng hay test lỗi vẫn phải ghi. Cập nhật memory ngắn gọn. Đánh dấu PRD hoàn tất để lần sau không coi nó là mô tả hiện hành.

## Ranh giới module đang dùng

Đối chiếu source ngày 31/10/2026; đây là bản đồ cho phạm vi hiện tại, không phải sơ đồ toàn bộ sản phẩm.

| Hành vi | Nơi bắt đầu đọc code | Cách kiểm chứng |
| --- | --- | --- |
| Đọc PDF và ghi chú | `frontend/src/features/learn-hub/pages/BookReaderWorkspace.jsx`, `useBookReaderState.js`, `bookReaderModel.js` | UI reader; lưu/mở lại; nối trang, IME, A4 |
| Upload/kệ sách theo tài khoản | `src/risk_dashboard/modules/learning/api/personal_library.py`, `infrastructure/personal_library.py` | API có auth; tài khoản khác không đọc/xóa được |
| Kiểm tra/đọc nguồn sách | `src/risk_dashboard/modules/learning/api/reader_proxy.py` | HTTP lỗi thật; signature PDF; giới hạn redirect |
| Đường dẫn DB | `src/risk_dashboard/platform/database/config.py` | Chạy test trong process được cấp DB tạm trước import |
| Phản hồi frontend | `frontend/scripts/test-runner.mjs` | CLI trả lỗi nếu không có test hoặc option sai |

Khi refactor, giữ interface đủ nhỏ để gọi và kiểm thử một luồng hoàn chỉnh. Không cần thêm wrapper nếu nó chỉ chuyển tiếp tham số. Đây là cách áp dụng [deep modules của tác giả](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) vào các ranh giới trên.

## Lệnh thực tế

Từ root, kiểm tra thư viện PDF:

```sh
.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/test_personal_library.py tests/test_book_source_availability.py tests/test_reader_proxy.py
```

Runner dùng chính Python được gọi; trong CI dùng `python`. Nó đặt cả ba biến DB, tắt dotenv, chuyển cache/pytest temp/uploads có cấu hình sang thư mục tạm, tắt scheduler, ghi log/report và dọn runtime. Timeout mặc định 600 giây; thay bằng `--timeout 1200` **trước** dấu `--` khi cần. Report nằm dưới `output/qa/isolated-tests/<run-id>/`.

Đây không phải sandbox hệ điều hành. Test tự mở đường dẫn cố định, thay biến môi trường hoặc gọi provider vẫn cần được đọc và cô lập riêng. Không chạy reset/crawler/repair trên dữ liệu thật để kiểm chứng. Không có backup trước sự cố DB lịch sử; các thay đổi này không khôi phục dữ liệu đó.

Từ `frontend/`, bộ kiểm tra đã có:

```sh
npm run test:unit
npm run lint
npm run lint:css
npm run build -- --emptyOutDir false
```

Lọc test theo chuỗi trong đường dẫn: `npm run test:unit -- --testPathPattern=reader`. Bộ lọc không có test phải thất bại. Không có bước `typecheck` toàn frontend hiện tại; không báo typecheck đã đạt chỉ vì build thành công.

UI reader: dùng [hướng dẫn server QA tạm và browser flows](../memory/sessions/2026-10-31-reader-compact.md). Cần ghi rõ viewport/browser đã thử. CI đã cấu hình thêm frontend unit/CSS và dùng runner backend; chạy local không chứng minh pipeline GitHub đã chạy.

## Ngữ cảnh và trạng thái

- Điểm vào: [memory index](../memory/INDEX.md), rồi source/task liên quan. Không nạp toàn bộ lịch sử báo cáo.
- PRD là yêu cầu của một thay đổi; source là bằng chứng hệ thống hiện có. Cả hai cần đối chiếu khi khác nhau.
- Task mới bắt đầu từ `proposed`; chuyển `ready` khi phạm vi đã được người dùng cho phép và đủ thông tin. Task đã `done` chỉ giữ làm lịch sử.
- Task tiếp theo không tự được chạy chỉ vì có trong backlog. Không cài thêm framework/skill toàn cục, khởi chạy vòng agent vô hạn hoặc tạo issue bên ngoài từ tài liệu tham khảo.
