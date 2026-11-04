# Watchlist đa tài sản — 02/11/2026

Trạng thái: **verified trên source và QA tạm**, chưa triển khai localhost:8000.

## Lỗi và bản sửa

- API watchlist trước đây chỉ tra snapshot cổ phiếu Việt Nam; UI còn trộn thêm 300 mã cổ phiếu đứng đầu. Vì vậy mã crypto/FX/hàng hóa/chỉ số/phái sinh có thể lưu được nhưng không có giá, tên và đơn vị phù hợp.
- `application/watchlist_quotes.py` hợp nhất danh mục và snapshot của sáu nhóm, trả giá, biến động, loại tài sản, đơn vị, thời điểm và tình trạng nguồn. Đọc cache do scheduler cập nhật, không chặn thao tác lưu bằng việc gọi provider. Lỗi một nguồn không làm mất các nguồn khác; mã thiếu giá vẫn được giữ và hiện **Chưa có giá**.
- `BTC-USD`, `BTC/USD`, `EUR/USD`, mã Yahoo và alias chỉ số được tra về mã nội bộ. Mã đã lưu theo alias được tái sử dụng; đường DELETE nhận cả dấu `/` của dữ liệu cũ. Không di chuyển/xóa dữ liệu người dùng.
- `WatchlistPanel` dùng trực tiếp API đa tài sản; có gợi ý mã, lọc loại tài sản, tìm tên/mã, sắp xếp. Thêm mã xong xóa bộ lọc để mã mới hiện ngay. Không xếp hạng vốn hóa trộn VND với USD; hiển thị đơn vị vốn hóa riêng.
- Giá FX giữ đến 5 chữ số thập phân; tiền số giá nhỏ dùng độ chính xác thích ứng. Không làm tròn về 0 bằng formatter VND. Giá thiếu không được hiểu là giá/biến động 0. Quote cũ có thời điểm và nhãn **Giá lưu gần nhất**; quote `updated_at` ưu tiên hơn thời gian snapshot chung. Phái sinh dùng `as_of` của snapshot vì `quote_time` của provider không có múi giờ rõ ràng.
- Poll 15 giây khi trang hiển thị; tải lại khi quay về trang. Request cũ được hủy trước request mới/thao tác lưu. Lỗi cập nhật giữ danh sách và cho thử lại. Component được tạo lại theo phiên để tách dữ liệu tài khoản.
- `quote_last_price` và `quote_map` cho lệnh giấy/danh mục vẫn lấy VND equity. Kiểm thử chặn BTC trong luồng lệnh giấy hiện tại.

## Kiểm chứng

- **28 test backend khác nhau**: 12 ca watchlist mới, 10 ca market-portfolio/usage có sẵn, 6 ca VN feed. Chạy bằng `scripts/qa/run_isolated_tests.py`, DB tạm được đặt trước import. [Lượt đầu 21 ca](../../../../output/qa/isolated-tests/20261102T091509Z-4eeddeba/report.json), [12 ca bản cuối](../../../../output/qa/isolated-tests/20261102T092055Z-c3a71e98/report.json), [6 ca VN feed](../../../../output/qa/isolated-tests/20261102T091716Z-da06d748/report.json). Không cộng các lượt chạy lại vào tổng.
- [Frontend 162/162](../../../../output/qa/watchlist-fix/frontend.log); sau chỉnh cách bỏ số 0 cuối phần thập phân, [3 ca watchlist chạy lại đạt](../../../../output/qa/watchlist-fix/frontend-final.log). ESLint, CSS52, build và Ruff phạm vi đạt. [Lint](../../../../output/qa/watchlist-fix/lint-final.log), [CSS](../../../../output/qa/watchlist-fix/css-final.log), [build](../../../../output/qa/watchlist-fix/build-final.log).
- Chromium với **API watchlist/auth thật**, tài khoản thử trong DB tạm, bản sao snapshot 1.521 cổ phiếu, 90 mã global và 4 hợp đồng phái sinh. Provider network bị chặn; các API ngoài phạm vi được stub. [Harness](../../../../output/qa/watchlist-fix/server.py).
- Thao tác thêm FPT, BTC-USD, EUR/USD, XAU, SPX, VN30F1M, SHIB; đối chiếu số hiển thị với API thật; thử thêm trùng, reload, lọc kết hợp, tìm kiếm tên, thêm khi đang lọc, mã thiếu giá, sắp xếp null xuống cuối, xóa, lỗi503 và retry. [Bằng chứng](../../../../output/playwright/watchlist-fix/evidence.json).
- Đã xem ảnh **desktop1440** và **mobile390**, kiểm tra320 không tràn ngang toàn trang; bảng cuộn ngang trong vùng riêng. [Desktop](../../../../output/playwright/watchlist-fix/desktop.png), [mobile](../../../../output/playwright/watchlist-fix/mobile.png). Không có lỗi JavaScript không được xử lý trong các flow hoàn tất. Console503 là lỗi chủ động tạo để thử retry; có connection-refused khi nạp lại server QA giữa hai lượt, không phải bằng chứng API thành công.

- Đổi tài khoản trong khi GET của tài khoản cũ đang bị trì hoãn: xác minh phiên mới và mở lại tab, response cũ không xuất hiện; quay lại tài khoản đầu giữ danh sách. [Bằng chứng isolation](../../../../output/playwright/watchlist-fix/isolation.json). Kịch bản đầu timeout vì chưa mở lại tab sau remount toàn trang; sửa harness và chạy lại đạt.

## Giới hạn và vận hành

- `localhost:8000` trả connection refused khi bắt đầu, kể cả ngoài sandbox. Build kiểm chứng ở `/private/tmp/northstar-watchlist-fix-dist`, server QA cổng5192. Server QA đã dừng sau kiểm chứng. Không rebuild/restart stack8000, không deploy/push.
- Không xác minh provider trực tiếp, độ trễ thị trường hiện tại hoặc Safari/iOS thật. Snapshot có thể cũ; watchlist hiện rõ trạng thái và ngày giờ, không khẳng định realtime.
- Có thể lưu mã ngoài danh mục nhưng sẽ hiện **Chưa có giá**. Gợi ý liệt kê các mã trong catalog được hỗ trợ; không mở rộng provider cho mã/sàn mới.
- Chưa nối nút sao cục bộ ở bảng cổ phiếu với watchlist tài khoản; đây là luồng khác đã tồn tại trước tác vụ.
- Giữ nguyên staging trước phiên: SHA-256 `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`. Không reset/ghi DB live.
