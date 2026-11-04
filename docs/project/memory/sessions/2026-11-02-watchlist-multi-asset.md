# Watchlist đa tài sản — 02/11/2026

Status: **verified trên source/QA**. Theo yêu cầu sửa mã ngoài chứng khoán không hiển thị ở global-terminal.

- Root cause: API chỉ dùng snapshot VN; UI tải thêm top300 VN và áp formatter làm tròn VND cho mọi mã. Nguồn hiện hành: `market_portfolio/application/watchlist_quotes.py`, `services.py`, `api/public.py`, `frontend/.../WatchlistPanel.jsx`, `watchlistModel.js`.
- Resolver đọc snapshot sáu loại tài sản và catalog, giữ trạng thái/đơn vị/thời gian nguồn. Không giới hạn top300; không gọi provider trên thao tác watchlist. `VnMarketFeedProducer.snapshot(read_only=True)` hỗ trợ đọc cache mà không spawn refresh. Scheduler sẵn có chịu trách nhiệm làm mới.
- Chuẩn hóa alias BTC-USD/BTC/USD/EUR/USD/Yahoo, tái sử dụng alias đã lưu. DELETE path nhận dấu `/` trong mã legacy. Giá thiếu giữ row/hiện trạng thái; kiểu dữ liệu/đơn vị market cap không trộn VND và USD. Lệnh giấy vẫn dùng resolver equity VND riêng.
- UI có gợi ý mã, tìm/lọc loại, sort, giữ số nhỏ, thêm xong xóa filter đang che mã; poll15s khi visible; abort request cũ, error/retry giữ dữ liệu. Key session bảo đảm remount theo account. Mobile bảng cuộn ngang trong vùng riêng.
- **28 backend khác nhau**, **162 frontend**; sau formatter cuối chạy lại3 ca liên quan; lint/CSS52/build/Ruff phạm vi đạt. Chromium API/auth thật trên DB tạm, copy public snapshot; 6 nhóm luồng gồm7 mã, reload, filter, missing quote, xóa, retry503; ảnh desktop1440/mobile390 đã xem,320 không tràn toàn trang. [Report/evidence](../../qa/results/WATCHLIST_FIXES_2026_11_02.md).
- Chromium bổ sung: đổi tài khoản khi GET cũ đang trì hoãn không lộ dữ liệu; quay lại account trước giữ các mã. [Isolation](../../../../output/playwright/watchlist-fix/isolation.json). Server QA đã dừng.
- Localhost8000 connection refused; chưa rebuild/restart/deploy stack. Provider trực tiếp và Safari chưa kiểm chứng. Không ghi/reset DB thật. Staging SHA256 giữ nguyên `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`.
- Ngoài phạm vi: nút sao cục bộ ở bảng cổ phiếu chưa nối watchlist account; symbol ngoài catalog vẫn lưu được nhưng hiện chưa có giá. Không coi thiếu quote là0.
