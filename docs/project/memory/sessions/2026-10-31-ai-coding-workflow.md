# 2026-10-31 · Áp dụng workflow AI Coding

**Status: verified trên workspace** cho phạm vi bên dưới. Nguồn: yêu cầu áp dụng [video Matt Pocock](https://www.youtube.com/watch?v=-QFHIoCo-Ko&t=344s). Đọc transcript có timestamp và đối chiếu repo chính chủ; không xem được đầy đủ hình ảnh/phụ đề trực tiếp từ YouTube. Nguồn và cách áp dụng tại [workflow](../../engineering/WORKFLOW.md).

## Kết quả

- `AGENTS.md`: điểm vào memory/workflow, kiểm chứng theo hành vi, tách đề xuất khỏi yêu cầu đã chấp thuận, bảo vệ staging và dữ liệu; fallback CodeGraph đúng CLI hiện có.
- `docs/project/engineering/`: workflow gọn, mẫu PRD/task/review, PRD đã hoàn tất và backlog có dependencies/status. Các mục xuất/in notebook là **proposed**, chưa triển khai.
- `frontend/scripts/test-runner.mjs`: no match/empty collection trả 1; tham số sai/thiếu trả 2; giữ hai cách truyền filter và pass/fail thật. Test CLI dùng thư mục fixture tạm, không kiểm tra chuỗi implementation.
- `frontend/src/__tests__/test-helpers.js`: tắt WebSocket của Vite SSR để không mở cổng HMR trong unit test. Trước đó test vẫn pass nhưng log `EPERM` khi mở `0.0.0.0:24678`; lượt cuối không còn lỗi này.
- `scripts/qa/run_isolated_tests.py`: Python stdlib, cấp ba alias DB trước subprocess import, tắt dotenv/scheduler, chuyển pytest/cache/uploads có cấu hình sang temp, timeout theo process group, log và JSON report. Chặn `--basetemp` tùy ý để tránh pytest xóa thư mục người dùng.
- `.github/workflows/ci.yml`: thêm frontend unit/CSS, backend runner (timeout 1800 giây cho suite CI), runner contracts, upload artifact. Không push/deploy; CI remote chưa chạy.

## Kiểm chứng

| Phạm vi | Kết quả | Lệnh / artifact |
| --- | --- | --- |
| Frontend runner RED | 7 fail, 2 pass đúng lỗi trước sửa | `node --test frontend/src/__tests__/tooling/test-runner.test.js` |
| Backend runner RED | 4 fail vì CLI chưa tồn tại | `python -m unittest discover -s scripts/qa/tests -v` |
| Frontend toàn bộ hiện có | 148/148 pass | Từ frontend: `npm run test:unit`; `output/qa/workflow/frontend-tests.log` |
| Backend thư viện/reader | 68 pass | `.venv/bin/python scripts/qa/run_isolated_tests.py -- tests/test_personal_library.py tests/test_book_source_availability.py tests/test_reader_proxy.py` |
| CLI isolation/failure/timeout | 5/5 pass | `.venv/bin/python -m unittest discover -s scripts/qa/tests -v`; `output/qa/workflow/runner-tests.log` |
| Frontend lint/CSS/build | Pass; 51 CSS files | `npm run lint`, `npm run lint:css`, `npm run build -- --emptyOutDir false`; `output/qa/workflow/frontend-build.log` |
| Python mới | Ruff check/format pass | `scripts/qa/run_isolated_tests.py`, `scripts/qa/tests/test_isolated_runner.py` |
| CI/docs/diff | YAML parse, gate configuration, link check, diff whitespace | Kiểm tra local; không phải kết quả GitHub Actions |

Backend artifact: `output/qa/isolated-tests/20261031T153505Z-ec458e81/{pytest.log,report.json}`; runtime temp đã dọn. Evidence nằm trong `output/`, gitignored. Review thủ công theo AC1–AC5 và diff; không có reviewer độc lập hay chứng nhận full backend/coverage.

## Dữ liệu và giới hạn

- Contract tests truyền cả ba biến DB tới một file đối chứng và xác minh file đó giữ nguyên byte sau pass/fail/timeout; DB được mở ngay khi import nằm trong temp, pytest fixture cũng nằm trong đó. Đây là bằng chứng trực tiếp của cơ chế cấu hình.
- Đã thử so hash DB mặc định trước/sau; **hash khác nhau nên không báo DB live giữ nguyên**. Điều tra chỉ đọc: container `duanagenttaichinh-app-1` đang healthy, mount `data → /app/data`; Docker VM PID 33945 đang giữ DB. Suite kết thúc khoảng 15:35:43 UTC, DB tiếp tục ghi lúc 15:37:20 và 15:37:50 UTC khi không còn pytest. Vì có writer hoạt động, phép so hash live không xác định được riêng tác động của test. Quan sát ở `output/qa/workflow/{db-before.json,db-after.json,live-db-observation.json}`. Không dừng container, không reset/khôi phục DB.
- Runner cô lập các đường dẫn cấu hình, **không phải sandbox filesystem/network**. Test tự thay biến môi trường, ghi đường dẫn cứng hoặc gọi provider cần xem riêng trước khi chạy. Không mở rộng sang toàn bộ suite backend trong lượt này.
- Không đổi UI/logic tài chính trong phạm vi này; kiểm chứng thực tế là CLI/process/API test. Không chạy lại browser UI vì không đổi product UI.
- 116 staged entries sẵn có giữ nguyên; SHA-256 của `git diff --cached --raw` trước/sau: `38f8fe1906f7dcd23ef9f97d84a7bab92051ebf08cc60ac7bc90a6bcd21d41ec`. Không stage/commit công việc người dùng.
